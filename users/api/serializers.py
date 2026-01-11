from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from users.models import User


class OtpRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()


class OtpVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()


class BlacklistRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)  # type: ignore[arg-type]
            token.blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."}) from exc
        return attrs


class CustomerProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class SellerProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value
