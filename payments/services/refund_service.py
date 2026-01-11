from __future__ import annotations

# payments/services/refund_service.py
from decimal import Decimal
from typing import Optional

from django.db import transaction

from payments.gateways.selector import get_gateway
from payments.models import Transaction, TransactionType, TransactionStatus
from orders.models import Order
from users.models import User


class RefundError(Exception):
    pass


class RefundService:
    @staticmethod
    def _get_captured_amount(order: Order) -> Decimal:
        captured = Transaction.objects.filter(order=order, type=TransactionType.PAYMENT, status=TransactionStatus.SUCCEEDED)
        return sum((t.amount for t in captured), Decimal("0.00"))

    @staticmethod
    def _get_refunded_amount(order: Order) -> Decimal:
        refunded = Transaction.objects.filter(order=order, type=TransactionType.REFUND, status=TransactionStatus.SUCCEEDED)
        return sum((t.amount for t in refunded), Decimal("0.00"))

    @staticmethod
    @transaction.atomic
    def refund_order(
        *,
        order: Order,
        admin_user: User,
        amount: Decimal,
        reason: Optional[str],
        currency: str,
        idempotency_key: Optional[str],
    ) -> Transaction:
        if amount <= 0:
            raise RefundError("Refund amount must be > 0.")

        if idempotency_key:
            existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                if existing.status == TransactionStatus.SUCCEEDED:
                    return existing
                raise RefundError("Duplicate idempotency_key with non-succeeded transaction.")

        # pick first succeeded payment as the source (or you can choose latest)
        payment_tx = Transaction.objects.filter(
            order=order, type=TransactionType.PAYMENT, status=TransactionStatus.SUCCEEDED
        ).order_by("-created_at").first()
        if not payment_tx:
            raise RefundError("No captured payment exists for this order.")
        if not payment_tx.provider_ref:
            raise RefundError("Payment transaction missing provider reference.")

        captured = RefundService._get_captured_amount(order)
        refunded = RefundService._get_refunded_amount(order)
        refundable = captured - refunded
        if amount > refundable:
            raise RefundError(f"Refund exceeds refundable amount ({refundable}).")

        refund_tx = Transaction.objects.create(
            user=payment_tx.user,
            order=order,
            provider=payment_tx.provider,
            provider_ref=payment_tx.provider_ref,
            type=TransactionType.REFUND,
            status=TransactionStatus.PENDING,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            metadata={"reason": reason, "source_payment_tx_id": payment_tx.pk, "admin_id": admin_user.pk},
        )

        gateway = get_gateway()
        try:
            res = gateway.refund(
                provider_ref=payment_tx.provider_ref,
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key or f"order-{order.id}-refund-{refund_tx.pk}",
                metadata={"order_id": order.id, "admin_id": admin_user.id, "reason": reason},
            )
            refund_tx.provider_ref = res.refund_ref  # store refund ref
            refund_tx.status = TransactionStatus.SUCCEEDED
            refund_tx.save(update_fields=["provider_ref", "status"])
        except Exception as e:
            refund_tx.status = TransactionStatus.FAILED
            refund_tx.metadata = {**refund_tx.metadata, "error": str(e)}
            refund_tx.save(update_fields=["status", "metadata"])
            raise RefundError("Refund failed.") from e

        # Optional: mark order refunded if fully refunded
        # You can set a status enum like REFUNDED; keep consistent with your Orders.status.
        # If you have a status history model, add a record in the calling layer (admin workflow).
        return refund_tx
