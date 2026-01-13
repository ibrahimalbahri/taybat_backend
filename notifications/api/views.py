from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.api.serializers import (
    DeviceTokenRegisterSerializer,
    DeviceTokenSerializer,
)
from notifications.models import DeviceToken
from taybat_backend.typing import get_authenticated_user


class DeviceTokenRegisterView(APIView):
    """
    POST /api/notifications/device
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = DeviceTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        token = data["token"]
        device_type = data.get("device_type") or None

        device, _created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": user,
                "device_type": device_type,
                "is_active": True,
            },
        )

        return Response(DeviceTokenSerializer(device).data, status=status.HTTP_200_OK)
