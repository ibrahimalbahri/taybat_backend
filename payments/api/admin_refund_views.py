from __future__ import annotations

# payments/api/admin_refund_views.py
from decimal import Decimal

from django.db import transaction
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from payments.services.refund_service import RefundService, RefundError
from payments.api.admin_refund_serializers import AdminRefundSerializer
from loyalty.services.loyalty_service import LoyaltyService
from users.permissions import IsAdmin
from taybat_backend.typing import get_authenticated_user


class AdminOrderRefundView(generics.GenericAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminRefundSerializer

    @transaction.atomic
    def post(self, request: Request, order_id: int) -> Response:
        from orders.models import Order  # adjust path

        order = Order.objects.select_for_update().get(id=order_id)
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)

        amount: Decimal = s.validated_data["amount"]
        reason = s.validated_data.get("reason")
        idempotency_key = s.validated_data.get("idempotency_key") or None

        admin_user = get_authenticated_user(request)
        try:
            refund_tx = RefundService.refund_order(
                order=order,
                admin_user=admin_user,
                amount=amount,
                reason=reason,
                currency="EUR",
                idempotency_key=idempotency_key,
            )
        except RefundError as e:
            return Response({"detail": str(e)}, status=400)

        # Reverse loyalty if it was issued
        LoyaltyService.reverse_for_order(order=order, note=f"Reversed due to refund: {reason or ''}".strip())

        # Optionally update order.status / status history here if you have enums
        # Example:
        # order.status = "REFUNDED"
        # order.save(update_fields=["status"])
        # OrderStatusHistory.objects.create(order=order, status="REFUNDED")

        return Response(
            {
                "refund_transaction_id": refund_tx.id,
                "status": refund_tx.status,
                "amount": str(refund_tx.amount),
                "provider_ref": refund_tx.provider_ref,
            }
        )
