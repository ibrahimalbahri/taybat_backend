from __future__ import annotations

from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.admin_order_views import AdminOrderFilterSerializer
from orders.services.admin_orders import (
    build_seller_order_queryset,
    export_orders_to_excel_for_queryset,
    export_orders_to_pdf_for_queryset,
)
from users.permissions import IsSeller
from taybat_backend.typing import get_authenticated_user


class SellerOrderExportExcelView(APIView):
    """
    GET /api/seller/orders/export/excel/
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        parameters=[AdminOrderFilterSerializer],
        responses={
            200: serializers.DictField(
                child=serializers.CharField(),
                help_text="Export metadata including file path.",
            )
        },
        description="Export seller orders to an Excel file.",
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
        qs = build_seller_order_queryset(params, user)
        export = export_orders_to_excel_for_queryset(user, qs, params)
        return Response(
            {
                "export_id": export.id,
                "file_path": export.file_path,
            },
            status=status.HTTP_200_OK,
        )


class SellerOrderExportPdfView(APIView):
    """
    GET /api/seller/orders/export/pdf/
    """

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(
        parameters=[AdminOrderFilterSerializer],
        responses={
            200: serializers.DictField(
                child=serializers.CharField(),
                help_text="Export metadata including file path.",
            )
        },
        description="Export seller orders to a PDF file.",
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
        qs = build_seller_order_queryset(params, user)
        export = export_orders_to_pdf_for_queryset(user, qs, params)
        return Response(
            {
                "export_id": export.id,
                "file_path": export.file_path,
            },
            status=status.HTTP_200_OK,
        )
