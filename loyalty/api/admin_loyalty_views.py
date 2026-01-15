from __future__ import annotations

# loyalty/api/admin_loyalty_views.py
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from loyalty.services.loyalty_service import LoyaltyService
from loyalty.models import LoyaltyPoint
from users.permissions import IsAdmin
from .admin_loyalty_serializers import (
    AdminLoyaltyAdjustSerializer,
    AdminLoyaltyAdjustResponseSerializer,
    AdminLoyaltyListSerializer,
)
from taybat_backend.typing import get_authenticated_user


class AdminLoyaltyAdjustView(generics.GenericAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminLoyaltyAdjustSerializer

    @extend_schema(
        request=AdminLoyaltyAdjustSerializer,
        responses={200: AdminLoyaltyAdjustResponseSerializer},
        description="Adjust loyalty points for a user.",
    )
    def post(self, request: Request) -> Response:
        from users.models import User  # adjust

        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)

        user = User.objects.get(id=s.validated_data["user_id"])
        points = s.validated_data["points"]
        note = s.validated_data.get("note") or None

        admin_user = get_authenticated_user(request)
        lp = LoyaltyService.admin_adjust(admin_user=admin_user, user=user, points=points, note=note)
        return Response({"id": lp.id, "user_id": user.id, "points": lp.points, "source": lp.source, "created_at": lp.created_at})


class AdminLoyaltyListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminLoyaltyListSerializer

    def get_queryset(self) -> QuerySet[LoyaltyPoint]:
        qs = LoyaltyPoint.objects.select_related("user", "order").order_by("-created_at")
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        # optional date filters
        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter points by user id.",
            ),
        ],
        responses=AdminLoyaltyListSerializer(many=True),
        description="List loyalty points with optional user filter.",
    )
    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        qs = self.get_queryset()[:500]  # keep safe; add pagination if needed
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
