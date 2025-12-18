# loyalty/api/urls.py
from django.urls import path
from .admin_loyalty_views import AdminLoyaltyAdjustView, AdminLoyaltyListView
from .customer_loyalty_views import CustomerLoyaltyView

urlpatterns = [
    path("admin/loyalty/adjust/", AdminLoyaltyAdjustView.as_view(), name="admin-loyalty-adjust"),
    path("admin/loyalty/", AdminLoyaltyListView.as_view(), name="admin-loyalty-list"),
    path("customer/loyalty/", CustomerLoyaltyView.as_view(), name="customer-loyalty"),
]
