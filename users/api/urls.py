from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.api.views import (
    BlacklistRefreshView,
    OtpRequestView,
    OtpVerifyView,
    CustomerProfileView,
    SellerProfileView,
    DriverProfileView,
    AddressListCreateView,
    AddressDetailView,
    UserMeView,
)

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/token/blacklist/", BlacklistRefreshView.as_view(), name="token_blacklist"),
    path("auth/otp/request/", OtpRequestView.as_view(), name="otp_request"),
    path("auth/otp/verify/", OtpVerifyView.as_view(), name="otp_verify"),
    path("customer/profile/", CustomerProfileView.as_view(), name="customer-profile"),
    path("seller/profile/", SellerProfileView.as_view(), name="seller-profile"),
    path("driver/profile/", DriverProfileView.as_view(), name="driver-profile"),
    path("addresses/", AddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
    path("me/", UserMeView.as_view(), name="user-me"),
]
