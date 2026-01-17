from __future__ import annotations

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from orders.models import Order
from orders.api.serializers import OrderCreateUpdateSerializer, OrderOutputSerializer
from taybat_backend.typing import get_authenticated_user


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrderOutputSerializer(many=True)},
        description="List orders owned by the authenticated user.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=OrderCreateUpdateSerializer,
        responses={201: OrderCreateUpdateSerializer},
        description="Create an order for the authenticated user.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        return (
            Order.objects.filter(customer=user)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address", "driver")
            .prefetch_related("items__item")
            .order_by("-created_at")
        )

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method == "POST":
            return OrderCreateUpdateSerializer
        return OrderOutputSerializer

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        user = get_authenticated_user(self.request)
        serializer.save(customer=user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OrderOutputSerializer},
        description="Retrieve an order owned by the authenticated user.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=OrderCreateUpdateSerializer,
        responses={200: OrderCreateUpdateSerializer},
        description="Update an order owned by the authenticated user.",
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        request=OrderCreateUpdateSerializer,
        responses={200: OrderCreateUpdateSerializer},
        description="Replace an order owned by the authenticated user.",
    )
    def put(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().put(request, *args, **kwargs)

    @extend_schema(
        responses={204: None},
        description="Delete an order owned by the authenticated user.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().delete(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        return (
            Order.objects.filter(customer=user)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address", "driver")
            .prefetch_related("items__item")
        )

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method in {"PUT", "PATCH"}:
            return OrderCreateUpdateSerializer
        return OrderOutputSerializer
