from __future__ import annotations

# payments/api/admin_refund_serializers.py
from rest_framework import serializers


class AdminRefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)


class RefundResponseSerializer(serializers.Serializer):
    refund_transaction_id = serializers.IntegerField()
    status = serializers.CharField()
    amount = serializers.CharField()
    provider_ref = serializers.CharField(allow_null=True, required=False)
