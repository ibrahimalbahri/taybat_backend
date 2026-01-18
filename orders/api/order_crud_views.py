from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from orders.models import Order, OrderItem, OrderType
from orders.api.serializers import OrderCreateUpdateSerializer, OrderOutputSerializer
from sellers.models import Item
from users.models import Address, CustomerProfile, User
from taybat_backend.typing import get_authenticated_user


def _get_system_customer_for_seller(seller_user: User) -> User:
    email = f"seller-{seller_user.id}-system@taybat.local"
    phone = f"sys-seller-{seller_user.id}"
    name = f"{seller_user.name} System Customer"
    customer, created = User.objects.get_or_create(
        email=email,
        defaults={
            "name": name,
            "phone": phone,
            "is_verified": False,
        },
    )
    if created:
        customer.add_role("customer")
        CustomerProfile.objects.get_or_create(user=customer)
    else:
        if not customer.has_role("customer"):
            customer.add_role("customer")
        CustomerProfile.objects.get_or_create(user=customer)
    return customer


def _create_order_items_for_order(
    order: Order,
    items_data: list[dict[str, object]] | None,
    replace_existing: bool = False,
) -> None:
    if items_data is None:
        return
    if order.order_type != OrderType.FOOD:
        raise serializers.ValidationError("items are only allowed for FOOD orders.")
    if order.restaurant_id is None:
        raise serializers.ValidationError("restaurant is required for FOOD orders.")
    if not items_data:
        raise serializers.ValidationError("items cannot be empty for FOOD orders.")

    item_ids = [item["item_id"] for item in items_data]
    items_by_id = {
        item.id: item
        for item in Item.objects.filter(id__in=item_ids, restaurant=order.restaurant)
    }

    if replace_existing:
        OrderItem.objects.filter(order=order).delete()

    for line in items_data:
        item = items_by_id.get(line["item_id"])
        if not item:
            raise serializers.ValidationError("One or more items are invalid for this restaurant.")
        if not item.is_available:
            raise serializers.ValidationError(f"Item not available: {item.name}")
        OrderItem.objects.create(
            order=order,
            item=item,
            quantity=line["quantity"],
            customizations=line.get("customizations"),
        )


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
        responses={201: OrderOutputSerializer},
        description=(
            "Create an order for the authenticated user. "
            "FOOD orders must include items."
        ),
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        if user.has_role("seller"):
            user = _get_system_customer_for_seller(user)
        if user.has_role("driver"):
            return (
                Order.objects.filter(driver=user)
                .select_related("restaurant", "coupon", "pickup_address", "dropoff_address", "driver")
                .prefetch_related("items__item")
                .order_by("-created_at")
            )
            
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

    @transaction.atomic
    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(OrderOutputSerializer(order).data, status=201, headers=headers)

    def perform_create(self, serializer: serializers.BaseSerializer) -> Order:
        user = get_authenticated_user(self.request)
        customer = user
        if user.has_role("seller"):
            customer = _get_system_customer_for_seller(user)

        data = serializer.validated_data
        pickup_address_data = data.pop("pickup_address_data", None)
        dropoff_address_data = data.pop("dropoff_address_data", None)
        items_data = data.pop("items", None)

        if pickup_address_data:
            data["pickup_address"] = Address.objects.create(user=customer, **pickup_address_data)
        if dropoff_address_data:
            data["dropoff_address"] = Address.objects.create(user=customer, **dropoff_address_data)

        pickup_address = data.get("pickup_address")
        dropoff_address = data.get("dropoff_address")
        if pickup_address and pickup_address.user_id != customer.id:
            raise serializers.ValidationError("pickup_address does not belong to the order customer.")
        if dropoff_address and dropoff_address.user_id != customer.id:
            raise serializers.ValidationError("dropoff_address does not belong to the order customer.")

        order = serializer.save(customer=customer)
        _create_order_items_for_order(order, items_data)
        return order


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
        if user.has_role("seller"):
            user = _get_system_customer_for_seller(user)
        return (
            Order.objects.filter(customer=user)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address", "driver")
            .prefetch_related("items__item")
        )

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method in {"PUT", "PATCH"}:
            return OrderCreateUpdateSerializer
        return OrderOutputSerializer

    @transaction.atomic
    def perform_update(self, serializer: serializers.BaseSerializer) -> None:
        user = get_authenticated_user(self.request)
        customer = user
        if user.has_role("seller"):
            customer = _get_system_customer_for_seller(user)

        data = serializer.validated_data
        pickup_address_data = data.pop("pickup_address_data", None)
        dropoff_address_data = data.pop("dropoff_address_data", None)
        items_data = data.pop("items", None)

        if pickup_address_data:
            data["pickup_address"] = Address.objects.create(user=customer, **pickup_address_data)
        if dropoff_address_data:
            data["dropoff_address"] = Address.objects.create(user=customer, **dropoff_address_data)

        pickup_address = data.get("pickup_address")
        dropoff_address = data.get("dropoff_address")
        if pickup_address and pickup_address.user_id != customer.id:
            raise serializers.ValidationError("pickup_address does not belong to the order customer.")
        if dropoff_address and dropoff_address.user_id != customer.id:
            raise serializers.ValidationError("dropoff_address does not belong to the order customer.")

        serializer.save()
        if items_data is not None:
            order = serializer.instance
            _create_order_items_for_order(order, items_data, replace_existing=True)
