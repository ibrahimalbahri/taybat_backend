from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api.serializers import AppLegalLinksSerializer, AppVersionResponseSerializer


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="current_version",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Current app version to determine force update.",
            ),
        ],
        responses={200: AppVersionResponseSerializer},
        description="Return app version settings and force-update flag.",
    )
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

    @extend_schema(
        responses={200: AppLegalLinksSerializer},
        description="Return dynamic links for privacy policy, terms, and support.",
    )
    def get(self, request: Request) -> Response:
        return Response(
            {
                "privacy_url": getattr(settings, "LEGAL_PRIVACY_URL", ""),
                "terms_url": getattr(settings, "LEGAL_TERMS_URL", ""),
                "support_url": getattr(settings, "LEGAL_SUPPORT_URL", ""),
            }
        )
