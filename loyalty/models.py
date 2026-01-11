# loyalty/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models


class LoyaltySource(models.TextChoices):
    ORDER = "ORDER", "Order"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT", "Admin adjustment"
    REVERSAL = "REVERSAL", "Reversal"


class LoyaltyPoint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loyalty_points")
    points = models.IntegerField()  # allow negative for reversals
    source = models.CharField(max_length=30, choices=LoyaltySource.choices)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="loyalty_points")
    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="loyalty_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["order"]),
        ]
