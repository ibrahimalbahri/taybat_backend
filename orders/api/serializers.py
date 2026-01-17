from __future__ import annotations

from decimal import Decimal
from rest_framework import serializers

from sellers.models import Restaurant, Item
from orders.models import Order, OrderItem
from users.api.serializers import AddressCreateUpdateSerializer


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

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
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
            "is_manual",
            "created_at",
            "items",
        ]


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    pickup_address_data = AddressCreateUpdateSerializer(write_only=True, required=False)
    dropoff_address_data = AddressCreateUpdateSerializer(write_only=True, required=False)

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
            "driver",
            "is_manual",
            "pickup_address_data",
            "dropoff_address_data",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "pickup_address": {"required": False, "allow_null": True},
            "dropoff_address": {"required": False, "allow_null": True},
        }

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        if self.instance is None:
            has_pickup = attrs.get("pickup_address") or attrs.get("pickup_address_data")
            has_dropoff = attrs.get("dropoff_address") or attrs.get("dropoff_address_data")
            if not has_pickup or not has_dropoff:
                raise serializers.ValidationError(
                    "pickup_address or pickup_address_data and dropoff_address or dropoff_address_data are required."
                )
        return attrs


class ExportResponseSerializer(serializers.Serializer):
    export_id = serializers.IntegerField()
    file_path = serializers.CharField()
