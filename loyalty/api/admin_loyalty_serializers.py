from __future__ import annotations

# loyalty/api/admin_loyalty_serializers.py
from rest_framework import serializers

class AdminLoyaltyAdjustSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    points = serializers.IntegerField()
    note = serializers.CharField(required=False, allow_blank=True)
