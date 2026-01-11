from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from sellers.models import Coupon, Restaurant
from sellers.api.seller_serializers import (
    SellerCouponCreateSerializer,
    SellerCouponUpdateSerializer,
    SellerCouponSerializer,
)
from users.permissions import IsSeller
from taybat_backend.typing import get_authenticated_user


class SellerCouponCreateView(APIView):
    """
    Create a coupon for a restaurant owned by the seller.
    """
    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        request=SellerCouponCreateSerializer,
        responses={201: SellerCouponSerializer},
        description="Create a coupon for a seller-owned restaurant.",
    )
    def post(self, request: Request) -> Response:
        serializer = SellerCouponCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = get_authenticated_user(request)
        restaurant_id = data["restaurant_id"]

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, owner_user=user)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Restaurant not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if Coupon.objects.filter(restaurant=restaurant, code__iexact=data["code"]).exists():
            return Response(
                {"detail": "Coupon code already exists for this restaurant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        coupon = Coupon.objects.create(
            restaurant=restaurant,
            title=data["title"],
            description=data.get("description") or "",
            code=data["code"],
            percentage=data["percentage"],
            min_price=data.get("min_price") or 0,
            max_total_users=data.get("max_total_users"),
            max_per_customer=data.get("max_per_customer"),
            start_date=data["start_date"],
            end_date=data["end_date"],
            is_active=data.get("is_active", True),
        )

        return Response(
            SellerCouponSerializer(coupon).data,
            status=status.HTTP_201_CREATED,
        )


class SellerCouponUpdateView(APIView):
    """
    Update a coupon owned by the seller.
    """
    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        request=SellerCouponUpdateSerializer,
        responses={200: SellerCouponSerializer},
        description="Update a coupon for a seller-owned restaurant.",
    )
    def patch(self, request: Request, pk: int) -> Response:
        serializer = SellerCouponUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not data:
            return Response({"detail": "No fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_authenticated_user(request)
        try:
            coupon = Coupon.objects.select_related("restaurant").get(
                id=pk, restaurant__owner_user=user
            )
        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Coupon not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "code" in data:
            exists = (
                Coupon.objects.filter(
                    restaurant=coupon.restaurant,
                    code__iexact=data["code"],
                )
                .exclude(id=coupon.id)
                .exists()
            )
            if exists:
                return Response(
                    {"detail": "Coupon code already exists for this restaurant."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        for field, value in data.items():
            setattr(coupon, field, value)
        coupon.save(update_fields=list(data.keys()))

        return Response(SellerCouponSerializer(coupon).data, status=status.HTTP_200_OK)
