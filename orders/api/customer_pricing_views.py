from __future__ import annotations

from decimal import Decimal
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from users.permissions import IsCustomer
from users.models import Address
from orders.models import OrderType
from orders.api.pricing_serializers import (
    TaxiPricePreviewSerializer,
    ShippingPricePreviewSerializer,
    PriceQuoteResponseSerializer,
)
from orders.services.pricing import calculate_quote
from taybat_backend.typing import get_authenticated_user


class TaxiPricePreviewView(APIView):
    """
    Preview taxi pricing without creating an order.
    POST /api/customer/preview/taxi/
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(
        request=TaxiPricePreviewSerializer,
        responses={200: PriceQuoteResponseSerializer},
        description="Preview taxi pricing based on addresses and vehicle type"
    )
    def post(self, request: Request) -> Response:
        serializer = TaxiPricePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_authenticated_user(request)

        # Load and validate addresses (must belong to current user)
        try:
            pickup_address = Address.objects.get(
                id=data["pickup_address_id"],
                user=user,
            )
            dropoff_address = Address.objects.get(
                id=data["dropoff_address_id"],
                user=user,
            )
        except Address.DoesNotExist:
            return Response(
                {"detail": "One or more addresses not found or do not belong to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate quote using pricing service
        try:
            quote = calculate_quote(
                order_type=OrderType.TAXI,
                pickup_lat=pickup_address.lat,
                pickup_lng=pickup_address.lng,
                dropoff_lat=dropoff_address.lat,
                dropoff_lng=dropoff_address.lng,
                vehicle_type=data["vehicle_type"],
                tip=data.get("tip", Decimal("0.00")),
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return quote as JSON (no DB writes)
        response_data = {
            "calculated_distance": quote.calculated_distance,
            "calculated_time": quote.calculated_time,
            "subtotal_amount": quote.subtotal_amount,
            "discount_amount": quote.discount_amount,
            "delivery_fee": quote.delivery_fee,
            "total_amount": quote.total_amount,
        }

        response_serializer = PriceQuoteResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.validated_data, status=status.HTTP_200_OK)


class ShippingPricePreviewView(APIView):
    """
    Preview shipping pricing without creating an order.
    POST /api/customer/preview/shipping/
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(
        request=ShippingPricePreviewSerializer,
        responses={200: PriceQuoteResponseSerializer},
        description="Preview shipping pricing based on addresses, delivery type, and package details"
    )
    def post(self, request: Request) -> Response:
        serializer = ShippingPricePreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_authenticated_user(request)

        # Load and validate addresses (must belong to current user)
        try:
            pickup_address = Address.objects.get(
                id=data["pickup_address_id"],
                user=user,
            )
            dropoff_address = Address.objects.get(
                id=data["dropoff_address_id"],
                user=user,
            )
        except Address.DoesNotExist:
            return Response(
                {"detail": "One or more addresses not found or do not belong to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Extract weight if provided (already Decimal from serializer)
        weight_kg = data.get("weight_kg")

        # Calculate quote using pricing service
        try:
            quote = calculate_quote(
                order_type=OrderType.SHIPPING,
                pickup_lat=pickup_address.lat,
                pickup_lng=pickup_address.lng,
                dropoff_lat=dropoff_address.lat,
                dropoff_lng=dropoff_address.lng,
                delivery_type=data["delivery_type"],
                weight_kg=weight_kg,
                tip=data.get("tip", Decimal("0.00")),
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return quote as JSON (no DB writes)
        response_data = {
            "calculated_distance": quote.calculated_distance,
            "calculated_time": quote.calculated_time,
            "subtotal_amount": quote.subtotal_amount,
            "discount_amount": quote.discount_amount,
            "delivery_fee": quote.delivery_fee,
            "total_amount": quote.total_amount,
        }

        response_serializer = PriceQuoteResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.validated_data, status=status.HTTP_200_OK)
