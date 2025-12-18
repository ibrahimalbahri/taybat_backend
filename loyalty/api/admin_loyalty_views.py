# loyalty/api/admin_loyalty_views.py
from rest_framework import generics, permissions
from rest_framework.response import Response

from loyalty.services.loyalty_service import LoyaltyService
from loyalty.models import LoyaltyPoint
from users.permissions import IsAdmin
from .admin_loyalty_serializers import AdminLoyaltyAdjustSerializer


class AdminLoyaltyAdjustView(generics.GenericAPIView):
    permission_classes = [IsAdmin]
    serializer_class = AdminLoyaltyAdjustSerializer

    def post(self, request):
        from users.models import User  # adjust

        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)

        user = User.objects.get(id=s.validated_data["user_id"])
        points = s.validated_data["points"]
        note = s.validated_data.get("note") or None

        lp = LoyaltyService.admin_adjust(admin_user=request.user, user=user, points=points, note=note)
        return Response({"id": lp.id, "user_id": user.id, "points": lp.points, "source": lp.source, "created_at": lp.created_at})


class AdminLoyaltyListView(generics.ListAPIView):
    permission_classes = [IsAdmin]

    def get_queryset(self): # type: ignore
        qs = LoyaltyPoint.objects.select_related("user", "order").order_by("-created_at")
        user_id = self.request.query_params.get("user_id") # type: ignore
        if user_id:
            qs = qs.filter(user_id=user_id)
        # optional date filters
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()[:500]  # keep safe; add pagination if needed
        data = [
            {
                "id": x.pk,
                "user_id": x.user_id, # type: ignore
                "order_id": x.order_id, # type: ignore
                "points": x.points,
                "source": x.source,
                "note": x.note,
                "created_at": x.created_at,
            }
            for x in qs
        ]
        return Response(data)
