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
)
from users.models import CustomerProfile, User
from users.permissions import IsCustomer, IsSeller
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
