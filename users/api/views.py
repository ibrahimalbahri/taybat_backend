from __future__ import annotations

import secrets
from typing import Any, cast
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.api.serializers import (
    BlacklistRefreshSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    CustomerProfileUpdateSerializer,
    SellerProfileUpdateSerializer,
    DriverProfileUpdateSerializer,
    DriverProfileSerializer,
    AddressSerializer,
    AddressCreateUpdateSerializer,
)
from users.models import Address, CustomerProfile, DriverProfile, User
from users.permissions import IsCustomer, IsSeller, IsDriver, IsAuthenticated
from taybat_backend.typing import get_authenticated_user


class BlacklistRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = BlacklistRefreshSerializer

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Refresh token blacklisted."}, status=status.HTTP_200_OK)


class OtpRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OtpRequestSerializer

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"detail": "Invalid phone or inactive user."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"detail": "Invalid phone or inactive user."}, status=status.HTTP_400_BAD_REQUEST)

        code_length = getattr(settings, "OTP_CODE_LENGTH", 6)
        max_value = 10 ** code_length
        code = str(secrets.randbelow(max_value)).zfill(code_length)

        user.otp_code_hash = make_password(code)
        user.otp_code_created_at = timezone.now()
        user.save(update_fields=["otp_code_hash", "otp_code_created_at"])

        response_data = {"detail": "OTP sent", "otp": code}
        if settings.DEBUG:
            response_data["otp"] = code
        return Response(response_data, status=status.HTTP_200_OK)


class OtpVerifyView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OtpVerifySerializer

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({"detail": "Invalid phone or code."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"detail": "Invalid phone or code."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.otp_code_hash or not user.otp_code_created_at:
            return Response({"detail": "Invalid phone or code."}, status=status.HTTP_400_BAD_REQUEST)

        ttl_seconds = getattr(settings, "OTP_CODE_TTL_SECONDS", 300)
        if timezone.now() - user.otp_code_created_at > timedelta(seconds=ttl_seconds):
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(code, user.otp_code_hash):
            return Response({"detail": "Invalid phone or code."}, status=status.HTTP_400_BAD_REQUEST)

        user.otp_code_hash = None
        user.otp_code_created_at = None
        user.save(update_fields=["otp_code_hash", "otp_code_created_at"])
        user.add_role("customer")
        CustomerProfile.objects.get_or_create(user=user)

        refresh = RefreshToken.for_user(user)
        access_token = cast(Any, refresh).access_token
        return Response(
            {"refresh": str(refresh), "access": str(access_token)},
            status=status.HTTP_200_OK,
        )


class CustomerProfileUpdateView(generics.GenericAPIView):
    permission_classes = [IsCustomer]
    serializer_class = CustomerProfileUpdateSerializer

    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        data = serializer.validated_data
        if not data:
            return Response({"detail": "No fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        for field in ("name", "phone", "age"):
            if field in data:
                setattr(user, field, data[field])

        user.save(update_fields=list(data.keys()))
        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_200_OK,
        )


class SellerProfileUpdateView(generics.GenericAPIView):
    permission_classes = [IsSeller]
    serializer_class = SellerProfileUpdateSerializer

    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = get_authenticated_user(request)
        data = serializer.validated_data
        if not data:
            return Response({"detail": "No fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        for field in ("name", "phone", "age"):
            if field in data:
                setattr(user, field, data[field])

        user.save(update_fields=list(data.keys()))
        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_200_OK,
        )


class DriverProfileUpdateView(generics.GenericAPIView):
    permission_classes = [IsDriver]
    serializer_class = DriverProfileUpdateSerializer

    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not data:
            return Response({"detail": "No fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_authenticated_user(request)
        try:
            profile = user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response({"detail": "Driver profile not found."}, status=status.HTTP_404_NOT_FOUND)

        user_fields = {"name", "phone", "age"}
        profile_fields = {
            "vehicle_type",
            "accepts_food",
            "accepts_shipping",
            "accepts_taxi",
            "driving_license",
            "id_document",
            "other_documents",
        }

        user_update_fields: list[str] = []
        profile_update_fields: list[str] = []

        for field in user_fields:
            if field in data:
                setattr(user, field, data[field])
                user_update_fields.append(field)

        for field in profile_fields:
            if field in data:
                setattr(profile, field, data[field])
                profile_update_fields.append(field)

        if user_update_fields:
            user.save(update_fields=user_update_fields)
        if profile_update_fields:
            profile.save(update_fields=profile_update_fields)

        return Response(
            DriverProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )


class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        return Address.objects.filter(user=user).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddressCreateUpdateSerializer
        return AddressSerializer

    def perform_create(self, serializer):
        user = get_authenticated_user(self.request)
        serializer.save(user=user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        user = get_authenticated_user(self.request)
        return Address.objects.filter(user=user)

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return AddressCreateUpdateSerializer
        return AddressSerializer
