from __future__ import annotations

from django.db import models
from django.conf import settings
from typing import TYPE_CHECKING


class Export(models.Model):
    """
    Stores metadata about admin-triggered exports (orders reports).
    """

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exports",
    )
    file_path = models.CharField(max_length=500)
    filter_params = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects: models.Manager["Export"] = models.Manager()

    if TYPE_CHECKING:
        id: int
        admin_id: int

    class Meta:
        verbose_name = "Export"
        verbose_name_plural = "Exports"
        indexes = [
            models.Index(fields=["admin", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Export({self.pk}) by {self.admin_id}"
