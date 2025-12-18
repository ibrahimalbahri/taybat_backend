from decimal import Decimal

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsCustomer
from users.models import Address
from orders.models import (
    Order,
    OrderType,
    OrderStatus,
    OrderStatusHistory,
    ShippingPackage,
)
from orders.api.checkout_serializers import (
    TaxiCheckoutSerializer,
    ShippingCheckoutSerializer,
)
from orders.api.serializers import OrderOutputSerializer
from orders.services.pricing import calculate_quote
from payments.models import PaymentMethod
from payments.services.payment_service import PaymentService, PaymentError


class TaxiCheckoutView(APIView):
    """
    Create a TAXI order for the authenticated customer.
    """

    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(
        request=TaxiCheckoutSerializer,
        responses={201: OrderOutputSerializer},
        description="Create a TAXI order for the authenticated customer",
    )
    @transaction.atomic
    def post(self, request):
        serializer = TaxiCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Load and validate addresses (must belong to current user)
        try:
            pickup_address = Address.objects.get(
                id=data["pickup_address_id"], user=request.user
            )
            dropoff_address = Address.objects.get(
                id=data["dropoff_address_id"], user=request.user
            )
        except Address.DoesNotExist:
            return Response(
                {"detail": "One or more addresses not found or do not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tip = data.get("tip", Decimal("0.00"))

        # Calculate quote using pricing service
        try:
            quote = calculate_quote(
                order_type=OrderType.TAXI,
                pickup_lat=pickup_address.lat,
                pickup_lng=pickup_address.lng,
                dropoff_lat=dropoff_address.lat,
                dropoff_lng=dropoff_address.lng,
                vehicle_type=data["requested_vehicle_type"],
                tip=tip,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create order
        order = Order.objects.create(
            order_type=OrderType.TAXI,
            customer=request.user,
            restaurant=None,
            status=OrderStatus.PENDING,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            requested_vehicle_type=data["requested_vehicle_type"],
            calculated_distance=quote.calculated_distance,
            calculated_time=quote.calculated_time,
            subtotal_amount=quote.subtotal_amount,
            discount_amount=quote.discount_amount,
            delivery_fee=quote.delivery_fee,
            tip=tip,
            total_amount=quote.total_amount,
        )
        # Capture payment (PCI-safe tokenized method)
        try:
            payment_method = PaymentMethod.objects.get(
                id=data["payment_method_id"],
                user=request.user,
            )
        except PaymentMethod.DoesNotExist:
            return Response(
                {"detail": "Payment method not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        idempotency_key = (data.get("idempotency_key") or "").strip() or None

        try:
            PaymentService.capture_order_payment(
                order=order,
                user=request.user,
                payment_method=payment_method,
                currency="EUR",
                idempotency_key=idempotency_key,
            )
        except PaymentError as e:
            # The whole view is @transaction.atomic, so raising/returning after failure is safe.
            # If you prefer, you can mark the order as PAYMENT_FAILED and save history here.
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Record initial status history
        OrderStatusHistory.objects.create(order=order, status=order.status)

        return Response(
            OrderOutputSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class ShippingCheckoutView(APIView):
    """
    Create a SHIPPING order for the authenticated customer.
    """

    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(
        request=ShippingCheckoutSerializer,
        responses={201: OrderOutputSerializer},
        description="Create a SHIPPING order for the authenticated customer",
    )
    @transaction.atomic
    def post(self, request):
        serializer = ShippingCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Load and validate addresses (must belong to current user)
        try:
            pickup_address = Address.objects.get(
                id=data["pickup_address_id"], user=request.user
            )
            dropoff_address = Address.objects.get(
                id=data["dropoff_address_id"], user=request.user
            )
        except Address.DoesNotExist:
            return Response(
                {"detail": "One or more addresses not found or do not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tip = data.get("tip", Decimal("0.00"))
        package_data = data["package"]

        # Calculate quote using pricing service
        try:
            quote = calculate_quote(
                order_type=OrderType.SHIPPING,
                pickup_lat=pickup_address.lat,
                pickup_lng=pickup_address.lng,
                dropoff_lat=dropoff_address.lat,
                dropoff_lng=dropoff_address.lng,
                delivery_type=data["requested_delivery_type"],
                weight_kg=package_data["weight_kg"],
                tip=tip,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create order
        order = Order.objects.create(
            order_type=OrderType.SHIPPING,
            customer=request.user,
            restaurant=None,
            status=OrderStatus.PENDING,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            requested_delivery_type=data["requested_delivery_type"],
            calculated_distance=quote.calculated_distance,
            calculated_time=quote.calculated_time,
            subtotal_amount=quote.subtotal_amount,
            discount_amount=quote.discount_amount,
            delivery_fee=quote.delivery_fee,
            tip=tip,
            total_amount=quote.total_amount,
        )
        # Capture payment (PCI-safe tokenized method)
        try:
            payment_method = PaymentMethod.objects.get(
                id=data["payment_method_id"],
                user=request.user,
            )
        except PaymentMethod.DoesNotExist:
            return Response(
                {"detail": "Payment method not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        idempotency_key = (data.get("idempotency_key") or "").strip() or None

        try:
            PaymentService.capture_order_payment(
                order=order,
                user=request.user,
                payment_method=payment_method,
                currency="EUR",
                idempotency_key=idempotency_key,
            )
        except PaymentError as e:
            # The whole view is @transaction.atomic, so raising/returning after failure is safe.
            # If you prefer, you can mark the order as PAYMENT_FAILED and save history here.
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
        # Create shipping package row
        ShippingPackage.objects.create(
            order=order,
            size=package_data["size"],
            weight=package_data["weight_kg"],
            content=package_data["content"],
        )

        # Record initial status history
        OrderStatusHistory.objects.create(order=order, status=order.status)

        return Response(
            OrderOutputSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


