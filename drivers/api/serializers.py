from rest_framework import serializers
from orders.models import Order, OrderStatus
from drivers.models import DriverProfile


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
    
    def get_distance(self, obj):
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

