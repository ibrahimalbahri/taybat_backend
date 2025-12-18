from django.urls import path
from drivers.api.views import (
    DriverOnlineToggleView,
    DriverSuggestedOrdersView,
    DriverAcceptOrderView,
    DriverRejectOrderView,
    DriverUpdateOrderStatusView,
)

urlpatterns = [
    path("drivers/toggle-online/", DriverOnlineToggleView.as_view(), name="driver-toggle-online"),
    path("drivers/suggested-orders/", DriverSuggestedOrdersView.as_view(), name="driver-suggested-orders"),
    path("drivers/accept-order/", DriverAcceptOrderView.as_view(), name="driver-accept-order"),
    path("drivers/reject-order/", DriverRejectOrderView.as_view(), name="driver-reject-order"),
    path("drivers/update-order-status/", DriverUpdateOrderStatusView.as_view(), name="driver-update-order-status"),
]

