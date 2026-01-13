from __future__ import annotations

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from users.permissions import IsAdmin, IsApprovedDriver
from users.models import DriverProfile, DriverStatus, User
from drivers.models import DriverLocation
from drivers.api import serializers
from users.api import serializers as user_serializers
from orders.services.eligibility import is_driver_eligible_for_order
from orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    OrderDriverSuggestion,
    OrderDispatchState,
    OrderType,
)
from loyalty.services.loyalty_service import LoyaltyService
from taybat_backend.typing import get_authenticated_user


class DriverCreateView(APIView):
    """
    Create a driver user and profile (admin-only).
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        request=serializers.DriverCreateSerializer,
        responses={201: user_serializers.DriverProfileSerializer},
        description="Create a driver user and profile.",
    )
    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = serializers.DriverCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, _created = User.objects.get_or_create_user(
            email=data["email"],
            name=data["name"],
            phone=data["phone"],
            age=data.get("age"),
        )
        user.add_role("driver")

        profile, created = DriverProfile.objects.get_or_create(
            user=user,
            defaults={
                "vehicle_type": data["vehicle_type"],
                "accepts_food": data.get("accepts_food", False),
                "accepts_shipping": data.get("accepts_shipping", False),
                "accepts_taxi": data.get("accepts_taxi", False),
                "driving_license": data.get("driving_license"),
                "id_document": data.get("id_document"),
                "other_documents": data.get("other_documents"),
                "status": DriverStatus.PENDING,
            },
        )
        if not created:
            profile.vehicle_type = data["vehicle_type"]
            profile.accepts_food = data.get("accepts_food", False)
            profile.accepts_shipping = data.get("accepts_shipping", False)
            profile.accepts_taxi = data.get("accepts_taxi", False)
            profile.driving_license = data.get("driving_license")
            profile.id_document = data.get("id_document")
            profile.other_documents = data.get("other_documents")
            profile.save()

        response_serializer = user_serializers.DriverProfileSerializer(profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class DriverOnlineToggleView(APIView):
    """
    Toggle driver online/offline status.
    """
    permission_classes = [IsAuthenticated, IsApprovedDriver]

    @extend_schema(
        request=serializers.DriverOnlineStatusSerializer,
        responses={200: serializers.DriverOnlineStatusResponseSerializer},
        description="Toggle driver online/offline status"
    )
    def post(self, request: Request) -> Response:
        serializer = serializers.DriverOnlineStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_online = serializer.validated_data["is_online"]

        user = get_authenticated_user(request)
        driver_profile, created = DriverProfile.objects.get_or_create(
            user=user,
            defaults={"vehicle_type": "BIKE"}  # Default, should be set during registration
        )

        driver_profile.is_online = is_online
        driver_profile.save(update_fields=["is_online"])

        return Response(
            {"is_online": driver_profile.is_online, "message": "Status updated successfully"},
            status=status.HTTP_200_OK
        )


class DriverLocationUpdateView(APIView):
    """
    Update driver's latest location.
    """
    permission_classes = [IsAuthenticated, IsApprovedDriver]

    @extend_schema(
        request=serializers.DriverLocationUpdateSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="Update the authenticated driver's latest location",
    )
    def post(self, request: Request) -> Response:
        serializer = serializers.DriverLocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = get_authenticated_user(request)
        now = timezone.now()
        now = timezone.now()

        DriverLocation.objects.update_or_create(
            driver=driver,
            defaults={
                "lat": serializer.validated_data["lat"],
                "lng": serializer.validated_data["lng"],
                "heading": serializer.validated_data.get("heading"),
                "speed": serializer.validated_data.get("speed"),
            },
        )

        return Response(
            {"message": "Location updated successfully"},
            status=status.HTTP_200_OK,
        )


class DriverSuggestedOrdersView(generics.ListAPIView):
    """
    Get list of suggested orders for the driver.
    GET /api/drivers/suggested-orders/
    Returns orders that have been suggested to this driver and are still available.
    """
    permission_classes = [IsAuthenticated, IsApprovedDriver]
    serializer_class = serializers.SuggestedOrderSerializer

    def get_queryset(self) -> QuerySet[Order]:
        driver = get_authenticated_user(self.request)
        now = timezone.now()
        now = timezone.now()
        
        # Get driver profile to check acceptance types
        try:
            driver_profile = driver.driver_profile
        except DriverProfile.DoesNotExist:
            return Order.objects.none()

        if driver_profile.status != DriverStatus.APPROVED:
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
            driver=driver,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
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

    def get_serializer_context(self) -> dict[str, object]:
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class DriverAcceptOrderView(APIView):
    """
    Accept an order with atomic locking to prevent race conditions.
    """
    permission_classes = [IsAuthenticated, IsApprovedDriver]

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
    def post(self, request: Request) -> Response:
        serializer = serializers.OrderAcceptRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]

        driver = get_authenticated_user(request)

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

        if order.customer_id == driver.id:
            return Response(
                {"detail": "You cannot accept your own order."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            driver_profile = driver.driver_profile
        except DriverProfile.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )
        if driver_profile.status != DriverStatus.APPROVED:
            return Response(
                {"detail": "Driver is not approved."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not is_driver_eligible_for_order(driver_profile=driver_profile, order=order):
            return Response(
                {"detail": "Driver is not eligible for this order type."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify driver was suggested this order
        suggestion = OrderDriverSuggestion.objects.filter(
            order=order,
            driver=driver,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).first()

        if not suggestion:
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

        suggestion.status = OrderDriverSuggestion.SuggestionStatus.ACCEPTED
        suggestion.responded_at = now
        suggestion.save(update_fields=["status", "responded_at"])

        OrderDriverSuggestion.objects.filter(
            order=order,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        ).exclude(id=suggestion.id).update(
            status=OrderDriverSuggestion.SuggestionStatus.EXPIRED,
            responded_at=now,
        )

        OrderDispatchState.objects.filter(order=order).update(is_active=False)

        return Response(
            {
                "message": "Order accepted successfully",
                "order_id": order.pk,
                "status": order.status,
            },
            status=status.HTTP_200_OK
        )


class DriverRejectOrderView(APIView):
    """
    Reject a suggested order.
    """
    permission_classes = [IsAuthenticated, IsApprovedDriver]

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
    def post(self, request: Request) -> Response:
        serializer = serializers.OrderAcceptRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]

        driver = get_authenticated_user(request)

        # Verify driver was suggested this order
        try:
            suggestion = OrderDriverSuggestion.objects.select_related("order").get(
                order_id=order_id,
                driver=driver,
                status=OrderDriverSuggestion.SuggestionStatus.SENT,
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

        suggestion.status = OrderDriverSuggestion.SuggestionStatus.REJECTED
        suggestion.responded_at = now
        suggestion.save(update_fields=["status", "responded_at"])

        pending_exists = OrderDriverSuggestion.objects.filter(
            order=order,
            status=OrderDriverSuggestion.SuggestionStatus.SENT,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).exists()
        if not pending_exists and order.status == OrderStatus.DRIVER_NOTIFICATION_SENT:
            order.status = OrderStatus.SEARCHING_FOR_DRIVER
            order.save(update_fields=["status"])
            OrderStatusHistory.objects.create(
                order=order,
                status=OrderStatus.SEARCHING_FOR_DRIVER,
            )
            OrderDispatchState.objects.update_or_create(
                order=order,
                defaults={"next_retry_at": now},
            )

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
    permission_classes = [IsAuthenticated, IsApprovedDriver]

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
    def post(self, request: Request) -> Response:
        serializer = serializers.OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]
        new_status = serializer.validated_data["status"]

        driver = get_authenticated_user(request)

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
        valid_transitions: dict[OrderStatus, list[OrderStatus]] = {
            OrderStatus.ACCEPTED: [OrderStatus.ON_THE_WAY],
            OrderStatus.ON_THE_WAY: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
        }

        current_status = OrderStatus(order.status)
        if current_status not in valid_transitions:
            return Response(
                {"detail": f"Cannot update status from {current_status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status_enum = OrderStatus(new_status)
        if new_status_enum not in valid_transitions[current_status]:
            return Response(
                {
                    "detail": f"Invalid status transition from {current_status} to {new_status}.",
                    "valid_transitions": valid_transitions[current_status],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status
        old_status = order.status
        order.status = new_status_enum
        order.save(update_fields=["status"])

        # Record status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status_enum
        )
        if new_status_enum == OrderStatus.COMPLETED:
            LoyaltyService.issue_for_order(order=order)

        return Response(
            {
                "message": f"Order status updated from {old_status} to {new_status}",
                "order_id": order.pk,
                "status": order.status,
            },
            status=status.HTTP_200_OK
        )
