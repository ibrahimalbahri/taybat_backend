from __future__ import annotations

from rest_framework import serializers

from sellers.models import Category, Item, Coupon


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
