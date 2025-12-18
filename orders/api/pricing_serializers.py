from decimal import Decimal
from rest_framework import serializers
from orders.models import VehicleType


class TaxiPricePreviewSerializer(serializers.Serializer):
    """Serializer for taxi price preview request."""
    pickup_address_id = serializers.IntegerField(
        help_text="ID of the pickup address (must belong to the current user)"
    )
    dropoff_address_id = serializers.IntegerField(
        help_text="ID of the dropoff address (must belong to the current user)"
    )
    vehicle_type = serializers.ChoiceField(
        choices=VehicleType.choices,
        help_text="Vehicle type for the taxi ride"
    )
    tip = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        help_text="Optional tip amount"
    )


class ShippingPricePreviewSerializer(serializers.Serializer):
    """Serializer for shipping price preview request."""
    pickup_address_id = serializers.IntegerField(
        help_text="ID of the pickup address (must belong to the current user)"
    )
    dropoff_address_id = serializers.IntegerField(
        help_text="ID of the dropoff address (must belong to the current user)"
    )
    delivery_type = serializers.ChoiceField(
        choices=VehicleType.choices,
        help_text="Delivery vehicle type"
    )
    weight_kg = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        help_text="Package weight in kilograms (optional, but recommended for accurate pricing)"
    )
    size = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Package size description (optional)"
    )
    content = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Package content description (optional)"
    )
    tip = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        help_text="Optional tip amount"
    )


class PriceQuoteResponseSerializer(serializers.Serializer):
    """Serializer for price quote response."""
    calculated_distance = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Calculated distance in kilometers"
    )
    calculated_time = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Estimated delivery time in seconds"
    )
    subtotal_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Subtotal amount (base fare/fee + delivery fee)"
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Discount amount (0 for v1)"
    )
    delivery_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Delivery/service fee"
    )
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount (subtotal + tip)"
    )

