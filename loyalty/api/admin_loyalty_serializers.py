from __future__ import annotations

# loyalty/api/admin_loyalty_serializers.py
from rest_framework import serializers

from loyalty.models import LoyaltyPoint

class AdminLoyaltyAdjustSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    points = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True)


class AdminLoyaltyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyPoint
        fields = ("id", "user_id", "order_id", "points", "source", "note", "created_at")
        read_only_fields = fields
