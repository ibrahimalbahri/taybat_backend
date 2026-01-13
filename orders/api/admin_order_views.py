from __future__ import annotations

from django.db.models import QuerySet
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from orders.models import Order, OrderStatusHistory
from orders.models_exports import Export
from orders.api.serializers import OrderOutputSerializer, ExportResponseSerializer
from orders.services.admin_orders import (
    build_admin_order_queryset,
    export_orders_to_excel,
    export_orders_to_pdf,
)
from taybat_backend.typing import get_authenticated_user


class AdminOrderFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    order_type = serializers.CharField(required=False)
    restaurant_id = serializers.IntegerField(required=False)
    driver_id = serializers.IntegerField(required=False)
    customer_id = serializers.IntegerField(required=False)
    from_ = serializers.DateTimeField(required=False, source="from")
    to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False)


class AdminOrderListView(generics.ListAPIView):
    """
    GET /api/admin/orders/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = OrderOutputSerializer

    @extend_schema(
        parameters=[AdminOrderFilterSerializer],
        responses=OrderOutputSerializer(many=True),
        description="Admin order dashboard with filters and pagination.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Order]:
        params: dict[str, object] = {
            "status": self.request.query_params.get("status"),
            "order_type": self.request.query_params.get("order_type"),
            "restaurant_id": self.request.query_params.get("restaurant_id"),
            "driver_id": self.request.query_params.get("driver_id"),
            "customer_id": self.request.query_params.get("customer_id"),
            "search": self.request.query_params.get("search"),
        }
        from_val = self.request.query_params.get("from")
        to_val = self.request.query_params.get("to")
        if from_val:
            params["from"] = parse_datetime(from_val)
        if to_val:
            params["to"] = parse_datetime(to_val)

        return build_admin_order_queryset(params)


class AdminOrderExportExcelView(APIView):
    """
    GET /api/admin/orders/export/excel/
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        parameters=[AdminOrderFilterSerializer],
        responses={200: ExportResponseSerializer},
        description="Export filtered orders to an Excel file.",
    )
    def get(self, request: Request) -> Response:
        params: dict[str, object] = {
            "status": request.query_params.get("status"),
            "order_type": request.query_params.get("order_type"),
            "restaurant_id": request.query_params.get("restaurant_id"),
            "driver_id": request.query_params.get("driver_id"),
            "customer_id": request.query_params.get("customer_id"),
            "search": request.query_params.get("search"),
        }
        from_val = request.query_params.get("from")
        to_val = request.query_params.get("to")
        if from_val:
            params["from"] = parse_datetime(from_val)
        if to_val:
            params["to"] = parse_datetime(to_val)

        user = get_authenticated_user(request)
        export = export_orders_to_excel(user, params)
        return Response(
            {
                "export_id": export.id,
                "file_path": export.file_path,
            },
            status=status.HTTP_200_OK,
        )


class AdminOrderExportPdfView(APIView):
    """
    GET /api/admin/orders/export/pdf/
    """

    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        parameters=[AdminOrderFilterSerializer],
        responses={200: ExportResponseSerializer},
        description="Export filtered orders to a PDF file.",
    )
    def get(self, request: Request) -> Response:
        params: dict[str, object] = {
            "status": request.query_params.get("status"),
            "order_type": request.query_params.get("order_type"),
            "restaurant_id": request.query_params.get("restaurant_id"),
            "driver_id": request.query_params.get("driver_id"),
            "customer_id": request.query_params.get("customer_id"),
            "search": request.query_params.get("search"),
        }
        from_val = request.query_params.get("from")
        to_val = request.query_params.get("to")
        if from_val:
            params["from"] = parse_datetime(from_val)
        if to_val:
            params["to"] = parse_datetime(to_val)

        user = get_authenticated_user(request)
        export = export_orders_to_pdf(user, params)
        return Response(
            {
                "export_id": export.id,
                "file_path": export.file_path,
            },
            status=status.HTTP_200_OK,
        )


class AdminOrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["status", "timestamp"]


class AdminOrderStatusHistoryView(generics.ListAPIView):
    """
    GET /api/admin/orders/{id}/status-history/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminOrderStatusHistorySerializer

    @extend_schema(
        responses=AdminOrderStatusHistorySerializer(many=True),
        description="Return status transition history for an order.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[OrderStatusHistory]:
        order_id = self.kwargs["pk"]
        return (
            OrderStatusHistory.objects.filter(order_id=order_id)
            .order_by("timestamp")
            .all()
        )
