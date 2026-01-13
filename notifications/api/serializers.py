from __future__ import annotations

from rest_framework import serializers

from notifications.models import DeviceToken


class DeviceTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField()
    device_type = serializers.CharField(required=False, allow_blank=True)


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "device_type", "is_active", "created_at", "last_seen_at"]
