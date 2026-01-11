from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


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
