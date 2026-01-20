from __future__ import annotations

from django.db import transaction
from django.db.models import Sum, F, QuerySet
from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsSeller
from sellers.models import Restaurant, Category, Item
from sellers.api.seller_serializers import (
    SellerCategorySerializer,
    SellerItemSerializer,
    SellerRestaurantSerializer,
    SellerRestaurantCreateUpdateSerializer,
)
from orders.models import Order, OrderStatus, OrderItem, OrderStatusHistory
from orders.api.serializers import OrderOutputSerializer
from taybat_backend.typing import get_authenticated_user
from users.models import User


def _get_seller_restaurants(user: User) -> QuerySet[Restaurant]:
    """
    Return queryset of restaurants owned by the given seller.
    """
    return Restaurant.objects.filter(owner_user=user)


class SellerOrderListView(generics.ListAPIView):
    """
    List orders for restaurants owned by the current seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = OrderOutputSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter orders by status.",
            ),
        ]
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        restaurants = _get_seller_restaurants(user)
        qs = (
            Order.objects.filter(restaurant__in=restaurants)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address")
            .prefetch_related("items__item")
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class SellerOrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single order for restaurants owned by the seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = OrderOutputSerializer

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        restaurants = _get_seller_restaurants(user)
        return (
            Order.objects.filter(restaurant__in=restaurants)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address")
            .prefetch_related("items__item")
        )


class SellerOrderAcceptView(APIView):
    """
    Restaurant staff accept an order (e.g. start preparation).
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        request=None,
        responses={200: OrderOutputSerializer},
        description="Accept an order for a restaurant owned by the seller.",
    )
    @transaction.atomic
    def post(self, request: Request, pk: int) -> Response:
        user = get_authenticated_user(request)
        try:
            order = (
                Order.objects.select_for_update()
                .select_related("restaurant")
                .get(
                    id=pk,
                    restaurant__owner_user=user,
                )
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found for your restaurants."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status != OrderStatus.PENDING:
            return Response(
                {"detail": f"Cannot accept order in status {order.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = OrderStatus.ACCEPTED
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status=order.status)

        return Response(OrderOutputSerializer(order).data, status=status.HTTP_200_OK)


class SellerOrderStatusUpdateSerializer(drf_serializers.Serializer):
    """
    Request schema for updating order status.
    """

    status = drf_serializers.CharField()


class SellerOrderStatusUpdateView(APIView):
    """
    Update order status by restaurant staff.
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        request=SellerOrderStatusUpdateSerializer,
        responses={200: OrderOutputSerializer},
        description="Update order status for a restaurant order (e.g. CANCELLED).",
    )
    @transaction.atomic
    def post(self, request: Request, pk: int) -> Response:
        user = get_authenticated_user(request)
        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"detail": "status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate status value
        valid_statuses = {choice[0] for choice in OrderStatus.choices}
        if new_status not in valid_statuses:
            return Response(
                {"detail": f"Invalid status: {new_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = (
                Order.objects.select_for_update()
                .select_related("restaurant")
                .get(
                    id=pk,
                    restaurant__owner_user=user,
                )
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found for your restaurants."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update and record history
        order.status = new_status
        order.save(update_fields=["status"])
        OrderStatusHistory.objects.create(order=order, status=new_status)

        return Response(OrderOutputSerializer(order).data, status=status.HTTP_200_OK)


class SellerCategoryListCreateView(generics.ListCreateAPIView):
    """
    List and create categories for a restaurant owned by the seller.

    Requires ?restaurant_id= query parameter on create and list.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerCategorySerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Restaurant id to scope categories to the seller's restaurant.",
            ),
        ]
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Restaurant id to create categories under the seller's restaurant.",
            ),
        ]
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_permissions(self) -> list[object]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def _get_restaurant(self) -> Restaurant | None:
        restaurant_id = self.request.query_params.get("restaurant_id")
        if not restaurant_id:
            return None
        try:
            if self.request.method == "GET":
                return Restaurant.objects.get(id=restaurant_id)
            user = get_authenticated_user(self.request)
            return Restaurant.objects.get(id=restaurant_id, owner_user=user)
        except Restaurant.DoesNotExist:
            return None

    def get_queryset(self) -> QuerySet[Category]:
        restaurant = self._get_restaurant()
        if not restaurant:
            return Category.objects.none()
        return restaurant.categories.all().order_by("view_order", "name") # type: ignore

    def perform_create(self, serializer: drf_serializers.BaseSerializer) -> None:
        restaurant = self._get_restaurant()
        if not restaurant:
            raise drf_serializers.ValidationError("Invalid or missing restaurant_id.")
        serializer.save(restaurant=restaurant)


class SellerCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a category owned by the seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerCategorySerializer

    @extend_schema(
        responses={
            204: None,
            409: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Delete a category owned by the seller.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        category = self.get_object()
        if category.items.exists():
            return Response(
                {"detail": "Category cannot be deleted because it contains items."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            category.delete()
        except ProtectedError:
            return Response(
                {"detail": "Category cannot be deleted because it is in use."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self) -> list[object]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self) -> QuerySet[Category]:
        if self.request.method == "GET":
            return Category.objects.all()
        user = get_authenticated_user(self.request)
        return Category.objects.filter(restaurant__owner_user=user)


class SellerItemListCreateView(generics.ListCreateAPIView):
    """
    List and create items for a restaurant owned by the seller.

    Requires ?restaurant_id= query parameter for create and list.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerItemSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Restaurant id to scope items to the seller's restaurant.",
            ),
        ]
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Restaurant id to create items under the seller's restaurant.",
            ),
        ]
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_permissions(self) -> list[object]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def _get_restaurant(self) -> Restaurant | None:
        try:
            restaurant_id = self.request.query_params.get("restaurant_id")
            if restaurant_id:
                if self.request.method == "GET":
                    return Restaurant.objects.get(id=restaurant_id)
                user = get_authenticated_user(self.request)
                return Restaurant.objects.get(id=restaurant_id, owner_user=user)
            if self.request.method == "GET":
                return None
            user = get_authenticated_user(self.request)
            return Restaurant.objects.get(owner_user=user)
        except Restaurant.DoesNotExist:
            return None

    def get_queryset(self) -> QuerySet[Item]:
        restaurant = self._get_restaurant()
        if not restaurant:
            return Item.objects.none()
        return restaurant.items.all().order_by("category__view_order", "view_order", "name")

    def perform_create(self, serializer: drf_serializers.BaseSerializer) -> None:
        restaurant = self._get_restaurant()
        if not restaurant:
            raise drf_serializers.ValidationError("Invalid or missing restaurant_id.")

        category = serializer.validated_data.get("category")
        if category.restaurant_id != restaurant.id:
            raise drf_serializers.ValidationError(
                "Category does not belong to this restaurant."
            )

        serializer.save(restaurant=restaurant)


class SellerItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an item owned by the seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerItemSerializer

    def get_permissions(self) -> list[object]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    @extend_schema(
        responses={
            204: None,
            409: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Delete an item owned by the seller.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        item = self.get_object()
        if item.order_items.exists():
            return Response(
                {"detail": "Item cannot be deleted because it is referenced by orders."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            item.delete()
        except ProtectedError:
            return Response(
                {"detail": "Item cannot be deleted because it is referenced by orders."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self) -> QuerySet[Item]:
        if self.request.method == "GET":
            return Item.objects.all()
        user = get_authenticated_user(self.request)
        return Item.objects.filter(restaurant__owner_user=user)


class SellerItemStatsView(APIView):
    """
    Simple item-level statistics for a restaurant owner.
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "item_id": {"type": "integer"},
                    "total_quantity": {"type": "integer"},
                    "total_orders": {"type": "integer"},
                    "total_revenue": {"type": "number", "format": "decimal"},
                },
            }
        },
        description="Return basic sales statistics for a menu item.",
    )
    def get(self, request: Request, pk: int) -> Response:
        user = get_authenticated_user(request)
        try:
            item = Item.objects.select_related("restaurant").get(
                id=pk, restaurant__owner_user=user
            )
        except Item.DoesNotExist:
            return Response(
                {"detail": "Item not found for your restaurants."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Only count completed/delivered orders
        qs = OrderItem.objects.filter(
            item=item,
            order__restaurant=item.restaurant,
            order__status__in=[OrderStatus.DELIVERED, OrderStatus.COMPLETED],
        )

        agg = qs.aggregate(
            total_quantity=Sum("quantity"),
            total_orders=Sum(1),
            total_revenue=Sum(F("quantity") * F("item__price")),
        )

        total_quantity = agg["total_quantity"] or 0
        total_orders = qs.values("order_id").distinct().count()
        total_revenue = agg["total_revenue"] or 0

        return Response(
            {
                "item_id": item.id,
                "total_quantity": total_quantity,
                "total_orders": total_orders,
                "total_revenue": str(total_revenue),
            },
            status=status.HTTP_200_OK,
        )


class SellerRestaurantListCreateView(generics.ListCreateAPIView):
    """
    List and create restaurants owned by the seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerRestaurantSerializer

    @extend_schema(
        responses={200: SellerRestaurantSerializer(many=True)},
        description="List restaurants owned by the seller.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=SellerRestaurantCreateUpdateSerializer,
        responses={201: SellerRestaurantSerializer},
        description="Create a new restaurant for the seller.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Restaurant]:
        user = get_authenticated_user(self.request)
        return Restaurant.objects.filter(owner_user=user).order_by("-created_at")

    def get_serializer_class(self) -> type[drf_serializers.BaseSerializer]:
        if self.request.method == "POST":
            return SellerRestaurantCreateUpdateSerializer
        return SellerRestaurantSerializer

    def perform_create(self, serializer: drf_serializers.BaseSerializer) -> None:
        user = get_authenticated_user(self.request)
        serializer.save(owner_user=user)


class SellerRestaurantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a restaurant owned by the seller.
    """

    permission_classes = [IsAuthenticated, IsSeller]
    serializer_class = SellerRestaurantSerializer

    @extend_schema(
        responses={200: SellerRestaurantSerializer},
        description="Retrieve a restaurant owned by the seller.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=SellerRestaurantCreateUpdateSerializer,
        responses={200: SellerRestaurantSerializer},
        description="Update a restaurant owned by the seller.",
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        request=SellerRestaurantCreateUpdateSerializer,
        responses={200: SellerRestaurantSerializer},
        description="Replace a restaurant owned by the seller.",
    )
    def put(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().put(request, *args, **kwargs)

    @extend_schema(
        responses={
            204: None,
            409: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Delete a restaurant owned by the seller.",
    )
    def delete(self, request: Request, *args: object, **kwargs: object) -> Response:
        restaurant = self.get_object()
        if restaurant.items.filter(order_items__isnull=False).exists():
            return Response(
                {
                    "detail": (
                        "Restaurant cannot be deleted because its items are referenced by orders."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        try:
            restaurant.delete()
        except ProtectedError:
            return Response(
                {"detail": "Restaurant cannot be deleted because it is in use."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self) -> QuerySet[Restaurant]:
        user = get_authenticated_user(self.request)
        return Restaurant.objects.filter(owner_user=user)

    def get_serializer_class(self) -> type[drf_serializers.BaseSerializer]:
        if self.request.method in {"PUT", "PATCH"}:
            return SellerRestaurantCreateUpdateSerializer
        return SellerRestaurantSerializer
