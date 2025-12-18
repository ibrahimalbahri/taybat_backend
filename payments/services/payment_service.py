# payments/services/payment_service.py
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from payments.gateways.selector import get_gateway
from payments.models import Transaction, TransactionType, TransactionStatus, PaymentProvider, PaymentMethod


class PaymentError(Exception):
    pass


class PaymentService:
    @staticmethod
    @transaction.atomic
    def capture_order_payment(*, order, user, payment_method: PaymentMethod, currency: str, idempotency_key: str | None):
        """
        Captures total_amount for the order, records PAYMENT and (optionally) TIP ledger entries.
        Idempotency: if idempotency_key already exists and SUCCEEDED, return existing tx.
        """
        if idempotency_key:
            existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                if existing.status == TransactionStatus.SUCCEEDED:
                    return existing
                # If it exists but failed/pending, treat as conflict or return it.
                raise PaymentError("Duplicate idempotency_key with non-succeeded transaction.")

        total_amount = Decimal(order.total_amount)
        if total_amount <= 0:
            raise PaymentError("Order total_amount must be > 0 to capture payment.")

        # Create base PAYMENT tx (PENDING)
        payment_tx = Transaction.objects.create(
            user=user,
            order=order,
            provider=payment_method.provider,
            type=TransactionType.PAYMENT,
            status=TransactionStatus.PENDING,
            amount=total_amount,
            currency=currency,
            idempotency_key=idempotency_key,
            metadata={"order_id": order.id, "captured_at": timezone.now().isoformat()},
        )

        gateway = get_gateway()
        try:
            res = gateway.capture(
                amount=total_amount,
                currency=currency,
                payment_method_token=payment_method.token,
                idempotency_key=idempotency_key or f"order-{order.id}-payment-{payment_tx.pk}",
                metadata={"order_id": order.id, "user_id": user.id},
            )
            payment_tx.provider_ref = res.provider_ref
            payment_tx.status = TransactionStatus.SUCCEEDED
            payment_tx.save(update_fields=["provider_ref", "status"])
        except Exception as e:
            payment_tx.status = TransactionStatus.FAILED
            payment_tx.metadata = {**payment_tx.metadata, "error": str(e)}
            payment_tx.save(update_fields=["status", "metadata"])
            raise PaymentError("Payment capture failed.") from e

        # If you want a separate TIP ledger entry, record it here but keep same provider_ref.
        tip = Decimal(order.tip or 0)
        if tip > 0:
            Transaction.objects.create(
                user=user,
                order=order,
                provider=payment_method.provider,
                provider_ref=payment_tx.provider_ref,
                type=TransactionType.TIP,
                status=TransactionStatus.SUCCEEDED,
                amount=tip,
                currency=currency,
                metadata={"linked_payment_tx_id": payment_tx.pk},
            )

        return payment_tx
