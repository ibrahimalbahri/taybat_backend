from __future__ import annotations

# payments/api/customer_payment_method_serializers.py
from typing import Any

from rest_framework import serializers
from payments.models import PaymentMethod, PaymentProvider


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["provider", "token", "brand", "last4", "exp_month", "exp_year", "is_default"]

    def validate_last4(self, value: str | None) -> str | None:
        if value and (len(value) != 4 or not value.isdigit()):
            raise serializers.ValidationError("last4 must be exactly 4 digits.")
        return value

    def validate_exp_month(self, value: int | None) -> int | None:
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("exp_month must be 1-12.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # PCI safety: reject common card fields if present in payload
        forbidden = {"pan", "card_number", "cvv", "cvc", "expiry", "exp"}
        for k in forbidden:
            if k in self.initial_data:
                raise serializers.ValidationError("Do not send card number/CVV to backend.")
        return attrs


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "provider", "brand", "last4", "exp_month", "exp_year", "is_default", "created_at"]


class PaymentMethodDefaultSerializer(serializers.Serializer):
    is_default = serializers.BooleanField()
