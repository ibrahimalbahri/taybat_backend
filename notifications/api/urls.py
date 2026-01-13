from django.urls import path

from notifications.api.views import DeviceTokenRegisterView


urlpatterns = [
    path("notifications/device", DeviceTokenRegisterView.as_view(), name="device-token-register"),
]
