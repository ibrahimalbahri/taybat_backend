from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


@dataclass(frozen=True)
class AppVersionConfig:
    latest_version: str
    min_supported_version: str
    update_url: Optional[str]


def _parse_version(version: str) -> tuple[int, ...]:
    parts = []
    for chunk in version.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _is_force_update(current_version: str, min_supported_version: str) -> bool:
    return _parse_version(current_version) < _parse_version(min_supported_version)


class AppVersionView(APIView):
    """
    GET /api/config/version
    """

    def get(self, request: Request) -> Response:
        current_version = request.query_params.get("current_version") or ""
        config = AppVersionConfig(
            latest_version=getattr(settings, "APP_LATEST_VERSION", "1.0.0"),
            min_supported_version=getattr(settings, "APP_MIN_VERSION", "1.0.0"),
            update_url=getattr(settings, "APP_UPDATE_URL", None),
        )

        force_update = False
        if current_version:
            force_update = _is_force_update(current_version, config.min_supported_version)

        return Response(
            {
                "latest_version": config.latest_version,
                "min_supported_version": config.min_supported_version,
                "force_update": force_update,
                "update_url": config.update_url,
            }
        )


class AppLegalLinksView(APIView):
    """
    GET /api/config/legal
    """

    def get(self, request: Request) -> Response:
        return Response(
            {
                "privacy_url": getattr(settings, "LEGAL_PRIVACY_URL", ""),
                "terms_url": getattr(settings, "LEGAL_TERMS_URL", ""),
                "support_url": getattr(settings, "LEGAL_SUPPORT_URL", ""),
            }
        )
