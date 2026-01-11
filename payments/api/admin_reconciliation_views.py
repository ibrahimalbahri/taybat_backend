from __future__ import annotations

# payments/api/admin_reconciliation_views.py
from decimal import Decimal

from django.db.models import Sum
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from payments.models import Transaction, TransactionType, TransactionStatus
from users.permissions import IsAdmin


class AdminReconciliationOrdersView(generics.GenericAPIView):
    permission_classes = [IsAdmin]

    def get(self, request: Request) -> Response:
        from orders.models import Order  # adjust

        qs = Order.objects.all().order_by("-created_at")
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        status = request.query_params.get("status")

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if status:
            qs = qs.filter(status=status)

        qs = qs[:500]

        order_ids = [o.pk for o in qs]
        tx = Transaction.objects.filter(order_id__in=order_ids, status=TransactionStatus.SUCCEEDED)

        captured = tx.filter(type=TransactionType.PAYMENT).values("order_id").annotate(total=Sum("amount"))
        refunded = tx.filter(type=TransactionType.REFUND).values("order_id").annotate(total=Sum("amount"))

        captured_map = {x["order_id"]: x["total"] for x in captured}
        refunded_map = {x["order_id"]: x["total"] for x in refunded}

        out = []
        for o in qs:
            cap = Decimal(captured_map.get(o.pk) or 0)
            ref = Decimal(refunded_map.get(o.pk) or 0)
            net = cap - ref
            out.append(
                {
                    "order_id": o.pk,
                    "order_type": getattr(o, "order_type", None),
                    "status": getattr(o, "status", None),
                    "captured": str(cap),
                    "refunded": str(ref),
                    "net": str(net),
                    "flag_mismatch": (cap > 0 and getattr(o, "status", "") in {"CANCELLED", "PAYMENT_FAILED"}) or (ref > 0 and net < 0),
                }
            )

        return Response(out)
