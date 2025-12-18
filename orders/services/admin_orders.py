"""
Admin-facing order dashboard and export services.
"""
import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from orders.models import Order
from orders.models_exports import Export


def build_admin_order_queryset(filters: Dict[str, Any]):
    """
    Build filtered queryset for admin order dashboard.
    """
    qs = (
        Order.objects.select_related(
            "restaurant",
            "customer",
            "driver",
            "pickup_address",
            "dropoff_address",
            "coupon",
        )
        .prefetch_related("items__item")
        .all()
    )

    status = filters.get("status")
    if status:
        qs = qs.filter(status=status)

    order_type = filters.get("order_type")
    if order_type:
        qs = qs.filter(order_type=order_type)

    restaurant_id = filters.get("restaurant_id")
    if restaurant_id:
        qs = qs.filter(restaurant_id=restaurant_id)

    driver_id = filters.get("driver_id")
    if driver_id:
        qs = qs.filter(driver_id=driver_id)

    customer_id = filters.get("customer_id")
    if customer_id:
        qs = qs.filter(customer_id=customer_id)

    created_from = filters.get("from")
    if created_from:
        qs = qs.filter(created_at__gte=created_from)

    created_to = filters.get("to")
    if created_to:
        qs = qs.filter(created_at__lte=created_to)

    search = filters.get("search")
    if search:
        q = Q(id__icontains=search)
        q |= Q(customer__name__icontains=search)
        q |= Q(customer__phone__icontains=search)
        q |= Q(restaurant__name__icontains=search)
        qs = qs.filter(q)

    return qs.order_by("-created_at")


def _ensure_export_dir() -> str:
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir is None:
        base_dir = os.getcwd()
    export_dir = os.path.join(base_dir, "admin_exports")
    os.makedirs(export_dir, exist_ok=True)
    return export_dir


def export_orders_to_excel(admin_user, filters: Dict[str, Any]) -> Export:
    """
    Export filtered orders to an Excel file (tabular).
    """
    from openpyxl import Workbook

    qs = build_admin_order_queryset(filters)
    export_dir = _ensure_export_dir()
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    filename = f"orders-{timestamp}.xlsx"
    file_path = os.path.join(export_dir, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    headers = [
        "order_id",
        "order_type",
        "status",
        "restaurant",
        "customer",
        "driver",
        "subtotal",
        "discount",
        "delivery_fee",
        "tip",
        "total",
        "created_at",
    ]
    ws.append(headers)

    for order in qs:
        ws.append(
            [
                order.id,
                order.order_type,
                order.status,
                getattr(order.restaurant, "name", None),
                getattr(order.customer, "name", None),
                getattr(order.driver, "name", None) if order.driver_id else None,
                order.subtotal_amount or Decimal("0.00"),
                order.discount_amount,
                order.delivery_fee,
                order.tip,
                order.total_amount,
                order.created_at.isoformat(),
            ]
        )

    wb.save(file_path)

    export = Export.objects.create(
        admin=admin_user,
        file_path=file_path,
        filter_params=filters,
    )
    return export


def export_orders_to_pdf(admin_user, filters: Dict[str, Any]) -> Export:
    """
    Export filtered orders to a simple PDF table.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    qs = build_admin_order_queryset(filters)
    export_dir = _ensure_export_dir()
    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    filename = f"orders-{timestamp}.pdf"
    file_path = os.path.join(export_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "Orders Export")
    y -= 10 * mm

    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, f"Generated at: {timezone.now().isoformat()}")
    y -= 10 * mm

    headers = [
        "ID",
        "Type",
        "Status",
        "Restaurant",
        "Customer",
        "Driver",
        "Subtotal",
        "Discount",
        "Delivery",
        "Tip",
        "Total",
    ]
    c.setFont("Helvetica-Bold", 7)
    c.drawString(10 * mm, y, " | ".join(headers))
    y -= 6 * mm

    c.setFont("Helvetica", 7)
    for order in qs:
        line = " | ".join(
            [
                str(order.id),
                order.order_type,
                order.status,
                getattr(order.restaurant, "name", "") or "",
                getattr(order.customer, "name", "") or "",
                getattr(order.driver, "name", "") if order.driver_id else "",
                str(order.subtotal_amount or Decimal("0.00")),
                str(order.discount_amount),
                str(order.delivery_fee),
                str(order.tip),
                str(order.total_amount),
            ]
        )
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 7)
        c.drawString(10 * mm, y, line[:200])
        y -= 5 * mm

    c.showPage()
    c.save()

    export = Export.objects.create(
        admin=admin_user,
        file_path=file_path,
        filter_params=filters,
    )
    return export


