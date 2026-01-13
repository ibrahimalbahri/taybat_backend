from __future__ import annotations

from rest_framework import serializers


class AdminReconciliationRowSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    order_type = serializers.CharField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    captured = serializers.CharField()
    refunded = serializers.CharField()
    net = serializers.CharField()
    flag_mismatch = serializers.BooleanField()
