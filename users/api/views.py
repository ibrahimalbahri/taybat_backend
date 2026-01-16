from __future__ import annotations

import secrets
from typing import Any, cast
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from users.api.serializers import (
    BlacklistRefreshSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    DetailResponseSerializer,
    OtpRequestResponseSerializer,
    OtpVerifyResponseSerializer,
    CustomerProfileUpdateSerializer,
    SellerProfileUpdateSerializer,
    DriverProfileUpdateSerializer,
    DriverProfileSerializer,
    AddressSerializer,
    AddressCreateUpdateSerializer,
    UserMeSerializer,
    UserMeUpdateSerializer,
    BasicProfileResponseSerializer,
)
from users.models import Address, CustomerProfile, DriverProfile, SellerProfile, User
from django.db.models import QuerySet
from users.permissions import IsCustomer, IsSeller, IsDriver, IsAuthenticated
from taybat_backend.typing import get_authenticated_user


class BlacklistRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = BlacklistRefreshSerializer

    @extend_schema(
        request=BlacklistRefreshSerializer,
        responses={200: DetailResponseSerializer},
        description="Blacklist a refresh token.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": "Refresh token blacklisted."}, status=status.HTTP_200_OK)


class OtpRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OtpRequestSerializer

    @extend_schema(
        request=OtpRequestSerializer,
        responses={200: OtpRequestResponseSerializer},
        description="Request an OTP to be sent to the user's phone.",
    )
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

    @extend_schema(
        request=OtpVerifySerializer,
        responses={200: OtpVerifyResponseSerializer},
        description="Verify OTP and return JWT tokens.",
    )
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


class CustomerProfileView(generics.GenericAPIView):
    permission_classes = [IsCustomer]
    serializer_class = CustomerProfileUpdateSerializer

    @extend_schema(
        responses={200: BasicProfileResponseSerializer},
        description="Retrieve customer profile basics (name, phone, age).",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            user.customer_profile
        except CustomerProfile.DoesNotExist:
            return Response({"detail": "Customer profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=CustomerProfileUpdateSerializer,
        responses={201: BasicProfileResponseSerializer},
        description="Create customer profile and optionally set basics (name, phone, age).",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        _profile, created = CustomerProfile.objects.get_or_create(user=user)

        update_fields: list[str] = []
        for field in ("name", "phone", "age"):
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)
        if update_fields:
            user.save(update_fields=update_fields)

        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        request=CustomerProfileUpdateSerializer,
        responses={200: BasicProfileResponseSerializer},
        description="Update customer profile basics (name, phone, age).",
    )
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

    @extend_schema(
        responses={204: None},
        description="Delete the authenticated customer's profile.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            profile = user.customer_profile
        except CustomerProfile.DoesNotExist:
            return Response({"detail": "Customer profile not found."}, status=status.HTTP_404_NOT_FOUND)

        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SellerProfileView(generics.GenericAPIView):
    permission_classes = [IsSeller]
    serializer_class = SellerProfileUpdateSerializer

    @extend_schema(
        responses={200: BasicProfileResponseSerializer},
        description="Retrieve seller profile basics (name, phone, age).",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            user.seller_profile
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Seller profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=SellerProfileUpdateSerializer,
        responses={201: BasicProfileResponseSerializer},
        description="Create seller profile and optionally set basics (name, phone, age).",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        _profile, created = SellerProfile.objects.get_or_create(user=user)

        update_fields: list[str] = []
        for field in ("name", "phone", "age"):
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)
        if update_fields:
            user.save(update_fields=update_fields)

        return Response(
            {"name": user.name, "phone": user.phone, "age": user.age},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        request=SellerProfileUpdateSerializer,
        responses={200: BasicProfileResponseSerializer},
        description="Update seller profile basics (name, phone, age).",
    )
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

    @extend_schema(
        responses={204: None},
        description="Delete the authenticated seller's profile.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            profile = user.seller_profile
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Seller profile not found."}, status=status.HTTP_404_NOT_FOUND)

        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DriverProfileView(generics.GenericAPIView):
    permission_classes = [IsDriver]
    serializer_class = DriverProfileUpdateSerializer

    def _apply_driver_updates(
        self,
        user: User,
        profile: DriverProfile,
        data: dict[str, object],
    ) -> None:
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

    @extend_schema(
        responses={200: DriverProfileSerializer},
        description="Retrieve the authenticated driver's profile.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            profile = user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response({"detail": "Driver profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(DriverProfileSerializer(profile).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=DriverProfileUpdateSerializer,
        responses={201: DriverProfileSerializer},
        description="Create the authenticated driver's profile.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        try:
            profile = user.driver_profile
            created = False
        except DriverProfile.DoesNotExist:
            if "vehicle_type" not in data:
                return Response(
                    {"detail": "vehicle_type is required to create a driver profile."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile = DriverProfile.objects.create(
                user=user,
                vehicle_type=data["vehicle_type"],
                accepts_food=data.get("accepts_food", False),
                accepts_shipping=data.get("accepts_shipping", False),
                accepts_taxi=data.get("accepts_taxi", False),
                driving_license=data.get("driving_license"),
                id_document=data.get("id_document"),
                other_documents=data.get("other_documents"),
            )
            created = True

        self._apply_driver_updates(user, profile, data)

        return Response(
            DriverProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        request=DriverProfileUpdateSerializer,
        responses={200: DriverProfileSerializer},
        description="Update driver profile and user basics.",
    )
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

        self._apply_driver_updates(user, profile, data)

        return Response(
            DriverProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={204: None},
        description="Delete the authenticated driver's profile.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        try:
            profile = user.driver_profile
        except DriverProfile.DoesNotExist:
            return Response({"detail": "Driver profile not found."}, status=status.HTTP_404_NOT_FOUND)

        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    @extend_schema(
        responses={200: AddressSerializer(many=True)},
        description="List saved addresses for the authenticated user.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=AddressCreateUpdateSerializer,
        responses={201: AddressSerializer},
        description="Create a new address for the authenticated user.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Address]:
        user = get_authenticated_user(self.request)
        return Address.objects.filter(user=user).order_by("-created_at")

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method == "POST":
            return AddressCreateUpdateSerializer
        return AddressSerializer

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        user = get_authenticated_user(self.request)
        serializer.save(user=user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    @extend_schema(
        responses={200: AddressSerializer},
        description="Retrieve a saved address.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=AddressCreateUpdateSerializer,
        responses={200: AddressSerializer},
        description="Update a saved address.",
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        request=AddressCreateUpdateSerializer,
        responses={200: AddressSerializer},
        description="Replace a saved address.",
    )
    def put(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().put(request, *args, **kwargs)

    @extend_schema(
        responses={204: None},
        description="Delete a saved address.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().delete(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Address]:
        user = get_authenticated_user(self.request)
        return Address.objects.filter(user=user)

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method in {"PUT", "PATCH"}:
            return AddressCreateUpdateSerializer
        return AddressSerializer


class UserMeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserMeSerializer},
        description="Return the authenticated user's profile summary.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        user = get_authenticated_user(request)
        return Response(UserMeSerializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserMeUpdateSerializer,
        responses={200: UserMeSerializer},
        description="Update the authenticated user's profile summary.",
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = UserMeUpdateSerializer(
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not data:
            return Response({"detail": "No fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_authenticated_user(request)
        update_fields: list[str] = []
        for field in ("name", "phone", "age"):
            if field in data:
                setattr(user, field, data[field])
                update_fields.append(field)
        if update_fields:
            user.save(update_fields=update_fields)

        return Response(UserMeSerializer(user).data, status=status.HTTP_200_OK)
