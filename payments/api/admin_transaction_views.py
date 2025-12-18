from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdmin
from payments.models import Transaction


class AdminTransactionFilterSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    order_id = serializers.IntegerField(required=False)
    type = serializers.CharField(required=False)
    from_ = serializers.DateTimeField(required=False, source="from")
    to = serializers.DateTimeField(required=False)


class AdminTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Transaction
        fields = ["id", "user", "user_email", "order", "type", "amount", "metadata", "created_at"]


class AdminTransactionListView(generics.ListAPIView):
    """
    GET /api/admin/transactions/
    """

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminTransactionSerializer

    @extend_schema(
        parameters=[AdminTransactionFilterSerializer],
        responses=AdminTransactionSerializer(many=True),
        description="Paginated admin transaction audit view.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Transaction.objects.select_related("user", "order").all()
        user_id = self.request.query_params.get("user_id")
        order_id = self.request.query_params.get("order_id")
        tx_type = self.request.query_params.get("type")
        from_val = self.request.query_params.get("from")
        to_val = self.request.query_params.get("to")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if order_id:
            qs = qs.filter(order_id=order_id)
        if tx_type:
            qs = qs.filter(type=tx_type)
        if from_val:
            qs = qs.filter(created_at__gte=from_val)
        if to_val:
            qs = qs.filter(created_at__lte=to_val)
        return qs.order_by("-created_at")


