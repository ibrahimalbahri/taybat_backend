from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class OtpRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()


class OtpVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()


class BlacklistRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."}) from exc
        return attrs
