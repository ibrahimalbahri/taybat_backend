from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.api.serializers import (
    DeviceTokenRegisterSerializer,
    DeviceTokenSerializer,
    NotificationCreateSerializer,
    NotificationSerializer,
    NotificationUpdateSerializer,
)
from notifications.models import DeviceToken, Notification
from taybat_backend.typing import get_authenticated_user


class DeviceTokenRegisterView(APIView):
    """
    POST /api/notifications/device
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=DeviceTokenRegisterSerializer,
        responses={200: DeviceTokenSerializer},
        description="Register or update an FCM device token for the authenticated user.",
    )
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


class NotificationListCreateView(APIView):
    """
    GET /api/notifications
    POST /api/notifications
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: NotificationSerializer(many=True)},
        description="List notifications for the authenticated user.",
    )
    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        notifications = Notification.objects.filter(recipient=user).order_by("-created_at")
        return Response(NotificationSerializer(notifications, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=NotificationCreateSerializer,
        responses={201: NotificationSerializer},
        description="Create a notification for the authenticated user.",
    )
    def post(self, request: Request) -> Response:
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        notification = Notification.objects.create(
            recipient=user,
            title=data["title"],
            body=data["body"],
            data=data.get("data"),
        )
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)


class NotificationDetailView(APIView):
    """
    GET /api/notifications/<id>
    PATCH /api/notifications/<id>
    DELETE /api/notifications/<id>
    """

    permission_classes = [IsAuthenticated]

    def _get_notification(self, user, notification_id):
        try:
            return Notification.objects.get(id=notification_id, recipient=user)
        except Notification.DoesNotExist:
            return None

    @extend_schema(
        responses={200: NotificationSerializer},
        description="Retrieve a notification for the authenticated user.",
    )
    def get(self, request: Request, notification_id: int) -> Response:
        user = get_authenticated_user(request)
        notification = self._get_notification(user, notification_id)
        if not notification:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=NotificationUpdateSerializer,
        responses={200: NotificationSerializer},
        description="Update a notification (e.g. mark read/unread).",
    )
    def patch(self, request: Request, notification_id: int) -> Response:
        serializer = NotificationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        notification = self._get_notification(user, notification_id)
        if not notification:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

        if "is_read" in data:
            notification.is_read = data["is_read"]
            notification.read_at = timezone.now() if data["is_read"] else None
            notification.save(update_fields=["is_read", "read_at"])

        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={204: None},
        description="Delete a notification for the authenticated user.",
    )
    def delete(self, request: Request, notification_id: int) -> Response:
        user = get_authenticated_user(request)
        notification = self._get_notification(user, notification_id)
        if not notification:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
