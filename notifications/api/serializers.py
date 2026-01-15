from __future__ import annotations

from rest_framework import serializers

from notifications.models import DeviceToken, Notification


class DeviceTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField()
    device_type = serializers.CharField(required=False, allow_blank=True)


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "device_type", "is_active", "created_at", "last_seen_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "data",
            "is_read",
            "read_at",
            "created_at",
        ]


class NotificationCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    body = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)


class NotificationUpdateSerializer(serializers.Serializer):
    is_read = serializers.BooleanField(required=False)
