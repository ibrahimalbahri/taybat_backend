from decimal import Decimal

from rest_framework import serializers

from orders.models import VehicleType


class TaxiCheckoutSerializer(serializers.Serializer):
    """
    Request payload for creating a TAXI order.
    """

    pickup_address_id = serializers.IntegerField()
    dropoff_address_id = serializers.IntegerField()
    requested_vehicle_type = serializers.ChoiceField(choices=VehicleType.choices)
    tip = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )


class ShippingPackageInputSerializer(serializers.Serializer):
    """
    Package details for SHIPPING checkout.
    """

    size = serializers.CharField(max_length=50)
    weight_kg = serializers.DecimalField(max_digits=8, decimal_places=2)
    content = serializers.CharField(max_length=255)


class ShippingCheckoutSerializer(serializers.Serializer):
    """
    Request payload for creating a SHIPPING order.
    """

    pickup_address_id = serializers.IntegerField()
    dropoff_address_id = serializers.IntegerField()
    requested_delivery_type = serializers.ChoiceField(choices=VehicleType.choices)
    tip = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
    )
    package = ShippingPackageInputSerializer()


