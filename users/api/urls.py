from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.api.views import (
    BlacklistRefreshView,
    OtpRequestView,
    OtpVerifyView,
    CustomerProfileUpdateView,
    SellerProfileUpdateView,
    DriverProfileUpdateView,
    AddressListCreateView,
    AddressDetailView,
)

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/token/blacklist/", BlacklistRefreshView.as_view(), name="token_blacklist"),
    path("auth/otp/request/", OtpRequestView.as_view(), name="otp_request"),
    path("auth/otp/verify/", OtpVerifyView.as_view(), name="otp_verify"),
    path("customer/profile/", CustomerProfileUpdateView.as_view(), name="customer-profile-update"),
    path("seller/profile/", SellerProfileUpdateView.as_view(), name="seller-profile-update"),
    path("driver/profile/", DriverProfileUpdateView.as_view(), name="driver-profile-update"),
    path("addresses/", AddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]
