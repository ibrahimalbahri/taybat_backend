from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from sellers.models import Restaurant, RestaurantStatus


class AdminRestaurantActivateView(APIView):
    """
    POST /api/admin/restaurants/{id}/activate/
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        request=None,
        responses={200: None},
        description="Activate a restaurant so it appears to customers and accepts orders.",
    )
    def post(self, request: Request, pk: int) -> Response:
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Restaurant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        restaurant.status = RestaurantStatus.ACTIVE
        restaurant.save(update_fields=["status"])
        return Response(status=status.HTTP_200_OK)


class AdminRestaurantDeactivateView(APIView):
    """
    POST /api/admin/restaurants/{id}/deactivate/
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        request=None,
        responses={200: None},
        description="Deactivate a restaurant; hide from customers and block new FOOD orders.",
    )
    def post(self, request: Request, pk: int) -> Response:
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Restaurant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        restaurant.status = RestaurantStatus.INACTIVE
        restaurant.save(update_fields=["status"])
        return Response(status=status.HTTP_200_OK)

