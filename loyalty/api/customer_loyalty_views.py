from __future__ import annotations

# loyalty/api/customer_loyalty_views.py
from django.db.models import Sum
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from loyalty.models import LoyaltyPoint
from users.permissions import IsCustomer
from taybat_backend.typing import get_authenticated_user


class CustomerLoyaltyView(generics.GenericAPIView):
    permission_classes = [IsCustomer]

    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        qs = LoyaltyPoint.objects.filter(user=user).order_by("-created_at")
        balance = qs.aggregate(total=Sum("points"))["total"] or 0
        rows = qs[:200]
        return Response(
            {
                "balance": balance,
                "entries": [
                    {
                        "id": x.pk,
                        "points": x.points,
                        "source": x.source,
                        "order_id": x.order_id,
                        "note": x.note,
                        "created_at": x.created_at,
                    }
                    for x in rows
                ],
            }
        )
