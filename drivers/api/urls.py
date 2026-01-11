from django.urls import path

from drivers.api.views import (
    DriverCreateView,
    DriverOnlineToggleView,
    DriverSuggestedOrdersView,
    DriverAcceptOrderView,
    DriverRejectOrderView,
    DriverUpdateOrderStatusView,
)
from drivers.api.admin_verification_views import (
    AdminDriverVerificationQueueView,
    AdminDriverVerifyView,
    AdminDriverVerificationHistoryView,
)


urlpatterns = [
    # Driver-facing endpoints
    path(
        "drivers/toggle-online/",
        DriverOnlineToggleView.as_view(),
        name="driver-toggle-online",
    ),
    path(
        "drivers/suggested-orders/",
        DriverSuggestedOrdersView.as_view(),
        name="driver-suggested-orders",
    ),
    path(
        "drivers/accept-order/",
        DriverAcceptOrderView.as_view(),
        name="driver-accept-order",
    ),
    path(
        "drivers/reject-order/",
        DriverRejectOrderView.as_view(),
        name="driver-reject-order",
    ),
    path(
        "drivers/update-order-status/",
        DriverUpdateOrderStatusView.as_view(),
        name="driver-update-order-status",
    ),
    path(
        "drivers/",
        DriverCreateView.as_view(),
        name="admin-driver-create",
    ),
    # Admin driver verification endpoints
    path(
        "admin/drivers/verification-queue/",
        AdminDriverVerificationQueueView.as_view(),
        name="admin-driver-verification-queue",
    ),
    path(
        "admin/drivers/<int:driver_id>/verify/",
        AdminDriverVerifyView.as_view(),
        name="admin-driver-verify",
    ),
    path(
        "admin/drivers/<int:driver_id>/verification-history/",
        AdminDriverVerificationHistoryView.as_view(),
        name="admin-driver-verification-history",
    ),
]
