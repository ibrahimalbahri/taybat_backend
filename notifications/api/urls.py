from django.urls import path

from notifications.api.views import (
    DeviceTokenRegisterView,
    NotificationDetailView,
    NotificationListCreateView,
)


urlpatterns = [
    path("notifications/device", DeviceTokenRegisterView.as_view(), name="device-token-register"),
    path("notifications", NotificationListCreateView.as_view(), name="notifications-list-create"),
    path(
        "notifications/<int:notification_id>",
        NotificationDetailView.as_view(),
        name="notifications-detail",
    ),
]
