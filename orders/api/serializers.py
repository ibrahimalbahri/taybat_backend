from decimal import Decimal
from rest_framework import serializers

from restaurants.models import Restaurant, Item
from orders.models import Order, OrderItem


class CartItemInputSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    customizations = serializers.JSONField(required=False)


class FoodCheckoutSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    pickup_address_id = serializers.IntegerField()
    dropoff_address_id = serializers.IntegerField()
    tip = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal("0.00"))
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    items = CartItemInputSerializer(many=True)

    def validate(self, attrs):
        if not attrs["items"]:
            raise serializers.ValidationError("Cart is empty.")
        return attrs


class OrderItemOutputSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "item", "item_name", "quantity", "customizations"]


class OrderOutputSerializer(serializers.ModelSerializer):
    items = OrderItemOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_type",
            "status",
            "restaurant",
            "coupon",
            "subtotal_amount",
            "discount_amount",
            "delivery_fee",
            "tip",
            "total_amount",
            "pickup_address",
            "dropoff_address",
            "requested_vehicle_type",
            "requested_delivery_type",
            "created_at",
            "items",
        ]
