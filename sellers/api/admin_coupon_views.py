from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from sellers.models import Coupon, CouponUsage


class AdminCouponSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "title",
            "description",
            "code",
            "percentage",
            "min_price",
            "max_total_users",
            "max_per_customer",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        ]

class ToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

class AdminCouponFilterSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField(required=False)
    active = serializers.BooleanField(required=False)
    from_ = serializers.DateTimeField(required=False, source="from")
    to = serializers.DateTimeField(required=False)
    code = serializers.CharField(required=False)


class AdminCouponListView(generics.ListAPIView):
    """
    GET /api/admin/coupons/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCouponSerializer

    @extend_schema(
        parameters=[AdminCouponFilterSerializer],
        responses=AdminCouponSerializer(many=True),
        description="List coupons with admin-level filters.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Coupon]:
        qs = Coupon.objects.select_related("restaurant").all()
        restaurant_id = self.request.query_params.get("restaurant_id")
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        active = self.request.query_params.get("active")
        if active is not None:
            if active.lower() == "true":
                qs = qs.filter(is_active=True)
            elif active.lower() == "false":
                qs = qs.filter(is_active=False)
        from_val = self.request.query_params.get("from")
        to_val = self.request.query_params.get("to")
        if from_val:
            qs = qs.filter(start_date__gte=from_val)
        if to_val:
            qs = qs.filter(end_date__lte=to_val)
        code = self.request.query_params.get("code")
        if code:
            qs = qs.filter(code__icontains=code)
        return qs.order_by("-created_at")


class AdminCouponDetailView(generics.RetrieveAPIView):
    """
    GET /api/admin/coupons/{id}/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCouponSerializer
    queryset = Coupon.objects.select_related("restaurant").all()

    @extend_schema(
        responses=AdminCouponSerializer,
        description="Retrieve coupon details.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)


class AdminCouponToggleView(APIView):
    """
    Enable/disable a coupon.
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    def _toggle(self, request: Request, pk: int, is_active: bool) -> Response:
        try:
            coupon = Coupon.objects.get(pk=pk)
        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Coupon not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        coupon.is_active = is_active
        coupon.save(update_fields=["is_active"])
        return Response({"is_active": coupon.is_active}, status=status.HTTP_200_OK)


class AdminCouponDisableView(AdminCouponToggleView):
    """
    POST /api/admin/coupons/{id}/disable/
    """

    @extend_schema(
        request=ToggleSerializer,
        responses={200: ToggleSerializer},
        description="Disable a coupon.",
    )
    def post(self, request: Request, pk: int) -> Response:
        serializer = ToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._toggle(request, pk, False)


class AdminCouponEnableView(AdminCouponToggleView):
    """
    POST /api/admin/coupons/{id}/enable/
    """

    @extend_schema(
        request=ToggleSerializer,
        responses={200: ToggleSerializer},
        description="Enable a coupon.",
    )
    def post(self, request: Request, pk: int) -> Response:
        serializer = ToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._toggle(request, pk, True)


class AdminCouponUsageSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True)

    class Meta:
        model = CouponUsage
        fields = ["id", "user", "user_email", "order_id", "created_at"]


class AdminCouponUsageView(generics.ListAPIView):
    """
    GET /api/admin/coupons/{id}/usage/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCouponUsageSerializer

    @extend_schema(
        responses=AdminCouponUsageSerializer(many=True),
        description="List coupon usage for audit.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[CouponUsage]:
        coupon_id = self.kwargs["pk"]
        qs = CouponUsage.objects.select_related("user", "order").filter(
            coupon_id=coupon_id
        )
        from_val = self.request.query_params.get("from")
        to_val = self.request.query_params.get("to")
        user_id = self.request.query_params.get("user_id")
        if from_val:
            qs = qs.filter(created_at__gte=from_val)
        if to_val:
            qs = qs.filter(created_at__lte=to_val)
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs.order_by("created_at")
