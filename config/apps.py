from __future__ import annotations

from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "config"

    def ready(self) -> None:
        from . import dash_apps  # noqa: F401
