from __future__ import annotations

from typing import Any

from rest_framework import serializers
from orders.models import Order, OrderStatus
from drivers.models import DriverProfile, VehicleType
from users.models import User


class DriverOnlineStatusSerializer(serializers.Serializer):
    """Serializer for online/offline toggle."""
    is_online = serializers.BooleanField()


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
        suggestion = obj.driver_suggestions.filter(
            driver=self.context["request"].user
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


class DriverProfileSerializer(serializers.ModelSerializer):
    """Serializer for driver profile details."""
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    age = serializers.IntegerField(source="user.age", read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "email",
            "name",
            "phone",
            "age",
            "roles",
            "status",
            "vehicle_type",
            "accepts_food",
            "accepts_shipping",
            "accepts_taxi",
            "is_online",
            "driving_license",
            "id_document",
            "other_documents",
            "created_at",
        ]

    def get_roles(self, obj: DriverProfile) -> list[str]:
        return list(obj.user.roles.values_list("name", flat=True))
