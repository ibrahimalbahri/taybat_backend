from __future__ import annotations

try:
    from .celery import app as celery_app
except ImportError:  # pragma: no cover - optional dependency for local tooling
    celery_app = None

__all__ = ("celery_app",)
