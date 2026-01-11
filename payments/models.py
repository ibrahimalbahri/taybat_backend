from __future__ import annotations

# payments/models.py
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class PaymentProvider(models.TextChoices):
    MOCK = "MOCK", "Mock"
    STRIPE = "STRIPE", "Stripe"  # ready for later


class TransactionType(models.TextChoices):
    PAYMENT = "PAYMENT", "Payment"
    REFUND = "REFUND", "Refund"
    TIP = "TIP", "Tip"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices, default=PaymentProvider.MOCK)
    token = models.CharField(max_length=255)  # provider PM token/id (treat as secret)
    brand = models.CharField(max_length=50, null=True, blank=True)
    last4 = models.CharField(max_length=4, null=True, blank=True)
    exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "provider", "token"], name="uq_paymentmethod_user_provider_token"),
        ]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        last4 = self.last4 or "----"
        return f"{self.user_id} {self.provider} ****{last4}"


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices, default=PaymentProvider.MOCK)
    provider_ref = models.CharField(max_length=255, null=True, blank=True)  # charge id / refund id
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    currency = models.CharField(max_length=3, default="EUR")
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} {self.status} {self.amount} {self.currency}"
