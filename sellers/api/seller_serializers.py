from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum, QuerySet
from django.utils import timezone
from rest_framework import serializers

from orders.models import Order, OrderStatus
from sellers.models import Category, Item, Coupon, Restaurant


class SellerCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for seller-side category management.
    """

    class Meta:
        model = Category
        fields = ["id", "name", "view_order"]


class SellerItemSerializer(serializers.ModelSerializer):
    """
    Serializer for seller-side item management.
    """

    class Meta:
        model = Item
        fields = [
            "id",
            "category",
            "name",
            "price",
            "image",
            "description",
            "ingredients",
            "customization_details",
            "view_order",
            "is_available",
        ]


class SellerCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id",
            "restaurant",
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


class SellerCouponCreateSerializer(serializers.ModelSerializer):
    restaurant_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Coupon
        fields = [
            "restaurant_id",
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
        ]


class SellerCouponUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
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
        ]


class SellerRestaurantSerializer(serializers.ModelSerializer):
    total_orders_today = serializers.SerializerMethodField()
    total_revenue_today = serializers.SerializerMethodField()
    pending_orders_count = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "address",
            "lat",
            "lng",
            "phone",
            "status",
            "created_at",
            "total_orders_today",
            "total_revenue_today",
            "pending_orders_count",
        ]
        read_only_fields = ["status", "created_at"]

    def _today_queryset(self, obj: Restaurant) -> QuerySet[Order]:
        today = timezone.localdate()
        return Order.objects.filter(restaurant=obj, created_at__date=today)

    def get_total_orders_today(self, obj: Restaurant) -> int:
        return self._today_queryset(obj).count()

    def get_total_revenue_today(self, obj: Restaurant) -> Decimal:
        total = self._today_queryset(obj).aggregate(total=Sum("total_amount"))["total"]
        return total or Decimal("0.00")

    def get_pending_orders_count(self, obj: Restaurant) -> int:
        return Order.objects.filter(restaurant=obj, status=OrderStatus.PENDING).count()


class SellerRestaurantCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["name", "address", "lat", "lng", "phone"]

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}
