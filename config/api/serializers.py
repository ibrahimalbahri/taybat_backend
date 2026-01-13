from __future__ import annotations

from rest_framework import serializers


class AppVersionResponseSerializer(serializers.Serializer):
    latest_version = serializers.CharField()
    min_supported_version = serializers.CharField()
    force_update = serializers.BooleanField()
    update_url = serializers.CharField(allow_null=True, required=False)


class AppLegalLinksSerializer(serializers.Serializer):
    privacy_url = serializers.CharField()
    terms_url = serializers.CharField()
    support_url = serializers.CharField()
