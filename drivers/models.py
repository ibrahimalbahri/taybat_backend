from __future__ import annotations

from django.db import models
from django.conf import settings


class DriverVerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class DriverVerification(models.Model):
    """
    Admin-driven verification events for drivers.

    Each record captures a single decision (approve/reject) plus notes.
    """

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="driver_verifications",
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_events",
    )
    status = models.CharField(
        max_length=20,
        choices=DriverVerificationStatus.choices,
        default=DriverVerificationStatus.PENDING,
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Driver Verification"
        verbose_name_plural = "Driver Verifications"
        indexes = [
            models.Index(fields=["driver", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"DriverVerification(driver={self.driver.id}, status={self.status})"
