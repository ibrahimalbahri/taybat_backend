from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from users.permissions import IsCustomer
from users.models import Address
from restaurants.models import Restaurant, Item
from orders.models import Order, OrderItem, OrderType, OrderStatus, OrderStatusHistory
from orders.api.serializers import FoodCheckoutSerializer, OrderOutputSerializer
from restaurants.services.coupons import apply_coupon_to_order, CouponError
from taybat_backend.typing import get_authenticated_user

class CustomerFoodCheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = FoodCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_authenticated_user(request)

        restaurant = Restaurant.objects.get(id=data["restaurant_id"])

        # Block checkout for inactive restaurants
        from restaurants.models import RestaurantStatus

        if restaurant.status != RestaurantStatus.ACTIVE:
            return Response(
                {"detail": "Restaurant is not accepting orders at the moment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pickup_address = Address.objects.get(id=data["pickup_address_id"], user=user)
        dropoff_address = Address.objects.get(id=data["dropoff_address_id"], user=user)

        # Fetch and validate items in one query
        item_ids = [i["item_id"] for i in data["items"]]
        items_by_id = {
            item.id: item
            for item in Item.objects.select_for_update().filter(id__in=item_ids, restaurant=restaurant)
        }

        # Validate cart items belong to this restaurant and are available
        subtotal = Decimal("0.00")
        normalized_items = []
        for cart_line in data["items"]:
            item = items_by_id.get(cart_line["item_id"])
            if not item:
                return Response({"detail": "One or more items are invalid for this restaurant."}, status=400)
            if not item.is_available:
                return Response({"detail": f"Item not available: {item.name}"}, status=400)

            line_total = (item.price * cart_line["quantity"]).quantize(Decimal("0.01"))
            subtotal += line_total
            normalized_items.append((item, cart_line["quantity"], cart_line.get("customizations")))

        # TODO: compute delivery_fee based on distance/pricing rules
        delivery_fee = Decimal("0.00")
        tip = data.get("tip", Decimal("0.00"))

        # Create order (coupon applied after create)
        order = Order.objects.create(
            order_type=OrderType.FOOD,
            customer=user,
            restaurant=restaurant,
            status=OrderStatus.PENDING,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            subtotal_amount=subtotal,
            discount_amount=Decimal("0.00"),
            delivery_fee=delivery_fee,
            tip=tip,
            total_amount=(subtotal + delivery_fee + tip).quantize(Decimal("0.01")),
        )

        # Create order items
        for item, qty, customizations in normalized_items:
            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=qty,
                customizations=customizations,
            )

        # Apply coupon if provided
        coupon_code = (data.get("coupon_code") or "").strip()
        if coupon_code:
            try:
                apply_coupon_to_order(order=order, user_id=user.id, code=coupon_code)
                order.refresh_from_db()
            except CouponError as e:
                # You may choose: fail checkout or allow checkout without coupon.
                # For v1, fail explicitly to avoid surprise totals.
                return Response({"detail": str(e)}, status=400)
        OrderStatusHistory.objects.create(order=order, status=order.status)


        return Response(OrderOutputSerializer(order).data, status=status.HTTP_201_CREATED)


class CustomerOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = OrderOutputSerializer

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        return (
            Order.objects
            .filter(customer=user)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address")
            .prefetch_related("items__item")
            .order_by("-created_at")
        )


class CustomerOrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = OrderOutputSerializer

    def get_queryset(self) -> QuerySet[Order]:
        user = get_authenticated_user(self.request)
        return (
            Order.objects
            .filter(customer=user)
            .select_related("restaurant", "coupon", "pickup_address", "dropoff_address")
            .prefetch_related("items__item")
        )
