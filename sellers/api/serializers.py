from __future__ import annotations

from rest_framework import serializers
from sellers.models import Restaurant, Category, Item


class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name", "address", "lat", "lng", "phone", "status"]


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id",
            "name",
            "price",
            "image",
            "description",
            "ingredients",
            "customization_details",
            "view_order",
            "is_available",
        ]


class CategoryWithItemsSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "view_order", "items"]


class RestaurantDetailSerializer(serializers.ModelSerializer):
    categories = CategoryWithItemsSerializer(many=True)

    class Meta:
        model = Restaurant
        fields = ["id", "name", "address", "lat", "lng", "phone", "status", "categories"]

class ItemSearchResultSerializer(serializers.ModelSerializer):
    restaurant_id = serializers.IntegerField(source="restaurant.id", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "name",
            "price",
            "image",
            "is_available",
            "category",
            "restaurant_id",
            "restaurant_name",
        ]
