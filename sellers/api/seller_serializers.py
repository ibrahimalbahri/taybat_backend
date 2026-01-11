from __future__ import annotations

from rest_framework import serializers

from sellers.models import Category, Item


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
