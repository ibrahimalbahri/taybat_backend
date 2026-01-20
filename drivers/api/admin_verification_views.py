from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from django.db.models import QuerySet
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from users.permissions import IsAdmin
from drivers.models import DriverVerification, DriverVerificationStatus
from users.models import DriverProfile
from drivers.services.verification import (
    verify_driver,
    DriverAlreadyVerified,
    DriverVerificationError,
)
from taybat_backend.typing import get_authenticated_user


class AdminDriverProfileSerializer(serializers.ModelSerializer):
    """
    Admin view of driver profile in verification queue.
    """

    email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "email",
            "name",
            "status",
            "vehicle_type",
            "accepts_food",
            "accepts_shipping",
            "accepts_taxi",
            "driving_license",
            "id_document",
            "other_documents",
            "created_at",
        ]


class AdminDriverVerificationSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin.email", read_only=True, allow_null=True)

    class Meta:
        model = DriverVerification
        fields = ["id", "status", "notes", "admin_email", "created_at"]


class AdminDriverVerificationActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[DriverVerificationStatus.APPROVED, DriverVerificationStatus.REJECTED]
    )
    notes = serializers.CharField(allow_blank=True, required=False)


class ErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AdminDriverVerificationQueueView(generics.ListAPIView):
    """
    GET /api/admin/drivers/verification-queue/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminDriverProfileSerializer

    @extend_schema(
        responses=AdminDriverProfileSerializer(many=True),
        description="List drivers awaiting verification (status=PENDING).",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[DriverProfile]:
        return DriverProfile.objects.filter(status="PENDING").select_related("user")


class AdminDriverVerifyView(APIView):
    """
    POST /api/admin/drivers/{driver_id}/verify/
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        request=AdminDriverVerificationActionSerializer,
        responses={
            200: AdminDriverVerificationSerializer,
            400: ErrorDetailSerializer,
            404: ErrorDetailSerializer,
            409: ErrorDetailSerializer,
        },
        description="Approve or reject a driver.",
    )
    def post(self, request: Request, driver_id: int) -> Response:
        action_serializer = AdminDriverVerificationActionSerializer(data=request.data)
        action_serializer.is_valid(raise_exception=True)
        data = action_serializer.validated_data

        admin_user = get_authenticated_user(request)
        try:
            result = verify_driver(
                admin_user=admin_user,
                driver_user_id=driver_id,
                status=data["status"],
                notes=data.get("notes") or "",
            )
        except DriverAlreadyVerified as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except DriverVerificationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            AdminDriverVerificationSerializer(result.verification).data,
            status=status.HTTP_200_OK,
        )


class AdminDriverVerificationHistoryView(generics.ListAPIView):
    """
    GET /api/admin/drivers/{driver_id}/verification-history/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminDriverVerificationSerializer

    @extend_schema(
        responses=AdminDriverVerificationSerializer(many=True),
        description="List verification history for a driver.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[DriverVerification]:
        driver_id = self.kwargs["driver_id"]
        return DriverVerification.objects.filter(driver_id=driver_id).select_related(
            "admin"
        ).order_by("created_at")
