# loyalty/api/customer_loyalty_views.py
from django.db.models import Sum
from rest_framework import generics, permissions
from rest_framework.response import Response
from loyalty.models import LoyaltyPoint
from users.permissions import IsCustomer


class CustomerLoyaltyView(generics.GenericAPIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        qs = LoyaltyPoint.objects.filter(user=request.user).order_by("-created_at")
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
                        "order_id": x.order_id, # type: ignore
                        "note": x.note,
                        "created_at": x.created_at,
                    }
                    for x in rows
                ],
            }
        )
