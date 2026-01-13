from __future__ import annotations

from rest_framework import serializers


class CustomerLoyaltyEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    points = serializers.IntegerField()
    source = serializers.CharField()
    order_id = serializers.IntegerField(allow_null=True)
    note = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()


class CustomerLoyaltyResponseSerializer(serializers.Serializer):
    balance = serializers.IntegerField()
    entries = CustomerLoyaltyEntrySerializer(many=True)
