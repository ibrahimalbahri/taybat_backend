from __future__ import annotations

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsSeller
from restaurants.models import Restaurant
from orders.models import Order, ManualOrder
from taybat_backend.typing import get_authenticated_user


class ManualOrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a ManualOrder record.

    We assume the actual Order has already been created via the
    appropriate checkout flow. This endpoint only logs that the
    order was created manually by staff and stores the scanned payload.
    """

    order_id = serializers.IntegerField()
    scanned_form_data = serializers.JSONField()


class SellerManualOrderCreateView(APIView):
    """
    Create a ManualOrder record for an existing order.

    POST /api/seller/orders/manual/
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        request=ManualOrderCreateSerializer,
        responses={201: None},
        description=(
            "Attach scanned form data to an existing order and mark it as a "
            "manual order created by seller staff."
        ),
    )
    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = ManualOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order_id = data["order_id"]
        user = get_authenticated_user(request)

        # Ensure order exists and belongs to one of the seller's restaurants
        try:
            order = (
                Order.objects.select_related("restaurant")
                .get(id=order_id, restaurant__owner_user=user)
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or does not belong to your restaurants."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent duplicate ManualOrder records for the same order
        if hasattr(order, "manual_order_record"):
            return Response(
                {"detail": "Manual order record already exists for this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ManualOrder.objects.create(
            staff_user=user,
            order=order,
            scanned_form_data=data["scanned_form_data"],
        )

        return Response(status=status.HTTP_201_CREATED)
