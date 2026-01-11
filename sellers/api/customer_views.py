from __future__ import annotations

from django.db.models import QuerySet
from typing import cast
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsCustomer
from sellers.models import Restaurant, Category, Item
from sellers.api.serializers import (
    RestaurantListSerializer,
    RestaurantDetailSerializer,
    ItemSearchResultSerializer
)


class CustomerRestaurantListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = RestaurantListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "address", "phone"]

    def get_queryset(self) -> QuerySet[Restaurant]:
        # Only show active restaurants (adjust if you want customers to see pending)
        return Restaurant.objects.filter(status="ACTIVE").order_by("id")


class CustomerRestaurantDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = RestaurantDetailSerializer
    queryset = (
        Restaurant.objects
        .all()
        .prefetch_related(
            # categories -> items
            "categories__items"
        )
    )

    def get_object(self) -> Restaurant:
        restaurant = cast(Restaurant, super().get_object())
        # Ensure nested ordering is deterministic
        restaurant.categories.all().order_by("view_order", "name")
        return restaurant



class CustomerItemSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = ItemSearchResultSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description", "ingredients"]

    def get_queryset(self) -> QuerySet[Item]:
        qs = (
            Item.objects
            .select_related("restaurant", "category")
            .filter(is_available=True, restaurant__status="ACTIVE")
        )

        restaurant_id = self.request.query_params.get("restaurant_id")
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)

        return qs.order_by("restaurant_id", "category_id", "view_order", "name")
