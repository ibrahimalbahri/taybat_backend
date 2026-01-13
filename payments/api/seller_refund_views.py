from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from payments.services.refund_service import RefundService, RefundError
from payments.api.admin_refund_serializers import AdminRefundSerializer, RefundResponseSerializer
from loyalty.services.loyalty_service import LoyaltyService
from users.permissions import IsSeller
from taybat_backend.typing import get_authenticated_user


class SellerOrderRefundView(generics.GenericAPIView):
    permission_classes = [IsSeller]
    serializer_class = AdminRefundSerializer

    @extend_schema(
        request=AdminRefundSerializer,
        responses={200: RefundResponseSerializer},
        description="Refund a seller order and return the refund transaction metadata.",
    )
    @transaction.atomic
    def post(self, request: Request, order_id: int) -> Response:
        from orders.models import Order

        seller_user = get_authenticated_user(request)
        try:
            order = Order.objects.select_for_update().get(
                id=order_id,
                restaurant__owner_user=seller_user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found for your restaurants."},
                status=status.HTTP_404_NOT_FOUND,
            )

        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)

        amount: Decimal = s.validated_data["amount"]
        reason = s.validated_data.get("reason")
        idempotency_key = s.validated_data.get("idempotency_key") or None

        try:
            refund_tx = RefundService.refund_order(
                order=order,
                admin_user=seller_user,
                amount=amount,
                reason=reason,
                currency="EUR",
                idempotency_key=idempotency_key,
            )
        except RefundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        LoyaltyService.reverse_for_order(
            order=order,
            note=f"Reversed due to refund: {reason or ''}".strip(),
        )

        return Response(
            {
                "refund_transaction_id": refund_tx.id,
                "status": refund_tx.status,
                "amount": str(refund_tx.amount),
                "provider_ref": refund_tx.provider_ref,
            }
        )
