from __future__ import annotations

from typing import Any

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from orders.models import Order, OrderStatus
from users.models import VehicleType, User


class DriverOnlineStatusSerializer(serializers.Serializer):
    """Serializer for online/offline toggle."""
    is_online = serializers.BooleanField()


class DriverOnlineStatusResponseSerializer(serializers.Serializer):
    is_online = serializers.BooleanField()
    message = serializers.CharField()


class DriverLocationUpdateSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)
    heading = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=359)
    speed = serializers.DecimalField(required=False, allow_null=True, max_digits=6, decimal_places=2)


class SuggestedOrderSerializer(serializers.ModelSerializer):
    """Serializer for suggested orders list."""
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True, allow_null=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    pickup_address = serializers.CharField(source="pickup_address.full_address", read_only=True)
    dropoff_address = serializers.CharField(source="dropoff_address.full_address", read_only=True)
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            "id",
            "order_type",
            "status",
            "restaurant_name",
            "customer_name",
            "pickup_address",
            "dropoff_address",
            "total_amount",
            "delivery_fee",
            "tip",
            "calculated_distance",
            "calculated_time",
            "requested_vehicle_type",
            "created_at",
            "distance",
        ]
    
    def get_distance(self, obj: Order) -> float | None:
        """Get distance from OrderDriverSuggestion if available."""
        now = timezone.now()
        suggestion = obj.driver_suggestions.filter(
            driver=self.context["request"].user,
            status=obj.driver_suggestions.model.SuggestionStatus.SENT,
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).first()
        if suggestion:
            return float(suggestion.distance_at_time)
        return None


class OrderAcceptRejectSerializer(serializers.Serializer):
    """Serializer for accept/reject actions."""
    order_id = serializers.IntegerField()


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for status updates."""
    order_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=[
        OrderStatus.ON_THE_WAY,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
    ])


class DriverCreateSerializer(serializers.Serializer):
    """Serializer for creating a driver user + profile."""
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    age = serializers.IntegerField(required=False, allow_null=True)
    vehicle_type = serializers.ChoiceField(choices=VehicleType.choices)
    accepts_food = serializers.BooleanField(required=False, default=False)
    accepts_shipping = serializers.BooleanField(required=False, default=False)
    accepts_taxi = serializers.BooleanField(required=False, default=False)
    driving_license = serializers.FileField(required=False, allow_null=True)
    id_document = serializers.FileField(required=False, allow_null=True)
    other_documents = serializers.FileField(required=False, allow_null=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value: str) -> str:
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value
