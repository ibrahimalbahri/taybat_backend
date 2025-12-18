from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from users.permissions import IsDriver
from drivers.models import DriverProfile
from drivers.api import serializers
from orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    OrderDriverSuggestion,
    OrderType,
)


class DriverOnlineToggleView(APIView):
    """
    Toggle driver online/offline status.
    """
    permission_classes = [IsAuthenticated, IsDriver]

    @extend_schema(
        request=serializers.DriverOnlineStatusSerializer,
        responses={200: serializers.DriverOnlineStatusSerializer},
        description="Toggle driver online/offline status"
    )
    def post(self, request):
        serializer = serializers.DriverOnlineStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_online = serializer.validated_data["is_online"]

        driver_profile, created = DriverProfile.objects.get_or_create(
            user=request.user,
            defaults={"vehicle_type": "BIKE"}  # Default, should be set during registration
        )

        driver_profile.is_online = is_online
        driver_profile.save(update_fields=["is_online"])

        return Response(
            {"is_online": driver_profile.is_online, "message": "Status updated successfully"},
            status=status.HTTP_200_OK
        )


class DriverSuggestedOrdersView(generics.ListAPIView):
    """
    Get list of suggested orders for the driver.
    GET /api/drivers/suggested-orders/
    Returns orders that have been suggested to this driver and are still available.
    """
    permission_classes = [IsAuthenticated, IsDriver]
    serializer_class = serializers.SuggestedOrderSerializer

    def get_queryset(self):
        driver = self.request.user
        
        # Get driver profile to check acceptance types
        try:
            driver_profile = driver.driver_profile
        except DriverProfile.DoesNotExist:
            return Order.objects.none()

        # Only show orders that:
        # 1. Have been suggested to this driver (via OrderDriverSuggestion)
        # 2. Are in SEARCHING_FOR_DRIVER or DRIVER_NOTIFICATION_SENT status
        # 3. Match driver's acceptance types
        # 4. Driver hasn't already accepted/rejected
        
        # Build filter for order types based on driver acceptance
        order_type_filter = Q()
        if driver_profile.accepts_food:
            order_type_filter |= Q(order_type=OrderType.FOOD)
        if driver_profile.accepts_shipping:
            order_type_filter |= Q(order_type=OrderType.SHIPPING)
        if driver_profile.accepts_taxi:
            order_type_filter |= Q(order_type=OrderType.TAXI)

        if not order_type_filter:
            return Order.objects.none()

        # Get orders suggested to this driver
        suggested_order_ids = OrderDriverSuggestion.objects.filter(
            driver=driver
        ).values_list("order_id", flat=True)

        queryset = Order.objects.filter(
            id__in=suggested_order_ids,
            status__in=[
                OrderStatus.SEARCHING_FOR_DRIVER,
                OrderStatus.DRIVER_NOTIFICATION_SENT,
            ],
            driver=None,  # Only show orders not yet accepted by any driver
        ).filter(order_type_filter).select_related(
            "restaurant",
            "customer",
            "pickup_address",
            "dropoff_address",
        ).prefetch_related(
            "driver_suggestions"
        ).order_by("-created_at")

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class DriverAcceptOrderView(APIView):
    """
    Accept an order with atomic locking to prevent race conditions.
    """
    permission_classes = [IsAuthenticated, IsDriver]

    @extend_schema(
        request=serializers.OrderAcceptRejectSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "order_id": {"type": "integer"},
                    "status": {"type": "string"},
                }
            },
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
            409: {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Accept an order with atomic locking to prevent race conditions"
    )
    @transaction.atomic
    def post(self, request):
        serializer = serializers.OrderAcceptRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]

        driver = request.user

        # Lock the order row to prevent concurrent acceptance
        try:
            order = Order.objects.select_for_update().get(
                id=order_id,
                status__in=[
                    OrderStatus.SEARCHING_FOR_DRIVER,
                    OrderStatus.DRIVER_NOTIFICATION_SENT,
                ],
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or no longer available."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if order was already assigned to another driver
        if order.driver is not None and order.driver != driver:
            return Response(
                {"detail": "Order has already been accepted by another driver."},
                status=status.HTTP_409_CONFLICT
            )

        # Verify driver was suggested this order
        suggestion_exists = OrderDriverSuggestion.objects.filter(
            order=order,
            driver=driver
        ).exists()

        if not suggestion_exists:
            return Response(
                {"detail": "This order was not suggested to you."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Assign order to driver and update status
        order.driver = driver
        order.status = OrderStatus.ACCEPTED
        order.save(update_fields=["driver", "status"])

        # Record status history
        OrderStatusHistory.objects.create(
            order=order,
            status=OrderStatus.ACCEPTED
        )

        return Response(
            {
                "message": "Order accepted successfully",
                "order_id": order.id,
                "status": order.status,
            },
            status=status.HTTP_200_OK
        )


class DriverRejectOrderView(APIView):
    """
    Reject a suggested order.
    """
    permission_classes = [IsAuthenticated, IsDriver]

    @extend_schema(
        request=serializers.OrderAcceptRejectSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "order_id": {"type": "integer"},
                }
            },
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Reject a suggested order"
    )
    @transaction.atomic
    def post(self, request):
        serializer = serializers.OrderAcceptRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]

        driver = request.user

        # Verify driver was suggested this order
        try:
            suggestion = OrderDriverSuggestion.objects.select_related("order").get(
                order_id=order_id,
                driver=driver
            )
            order = suggestion.order
        except OrderDriverSuggestion.DoesNotExist:
            return Response(
                {"detail": "This order was not suggested to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if order is still in a rejectable state
        if order.status not in [
            OrderStatus.SEARCHING_FOR_DRIVER,
            OrderStatus.DRIVER_NOTIFICATION_SENT,
        ]:
            return Response(
                {"detail": "Order is no longer in a rejectable state."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Remove the suggestion (driver has rejected)
        # The order will remain available for other drivers
        # Note: We could also mark this in a separate table, but for now
        # we'll just remove the suggestion so the driver doesn't see it again
        
        # Actually, we might want to keep the suggestion for analytics,
        # but mark it as rejected. For now, we'll just delete it.
        # In production, you might want a "rejected_at" timestamp instead.
        suggestion.delete()

        return Response(
            {
                "message": "Order rejected successfully",
                "order_id": order_id,
            },
            status=status.HTTP_200_OK
        )


class DriverUpdateOrderStatusView(APIView):
    """
    Update order status (on_the_way, delivered, completed) with history recording.
    """
    permission_classes = [IsAuthenticated, IsDriver]

    @extend_schema(
        request=serializers.OrderStatusUpdateSerializer,
        responses={
            200: {"type": "object", "properties": {
                "message": {"type": "string"},
                "order_id": {"type": "integer"},
                "status": {"type": "string"},
            }},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Update order status (on_the_way, delivered, completed) with history recording"
    )
    @transaction.atomic
    def post(self, request):
        serializer = serializers.OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]
        new_status = serializer.validated_data["status"]

        driver = request.user

        # Lock the order to prevent concurrent updates
        try:
            order = Order.objects.select_for_update().get(
                id=order_id,
                driver=driver,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or you are not assigned to this order."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate status transition
        valid_transitions = {
            OrderStatus.ACCEPTED: [OrderStatus.ON_THE_WAY],
            OrderStatus.ON_THE_WAY: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
        }

        current_status = order.status
        if current_status not in valid_transitions:
            return Response(
                {"detail": f"Cannot update status from {current_status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in valid_transitions[current_status]:
            return Response(
                {
                    "detail": f"Invalid status transition from {current_status} to {new_status}.",
                    "valid_transitions": valid_transitions[current_status],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status
        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status"])

        # Record status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status
        )

        return Response(
            {
                "message": f"Order status updated from {old_status} to {new_status}",
                "order_id": order.id,
                "status": order.status,
            },
            status=status.HTTP_200_OK
        )

