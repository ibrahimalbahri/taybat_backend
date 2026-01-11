from __future__ import annotations

# payments/api/customer_payment_method_views.py
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import generics, serializers
from rest_framework.request import Request
from rest_framework.response import Response

from payments.models import PaymentMethod
from users.permissions import IsCustomer
from .customer_payment_method_serializers import (
    PaymentMethodCreateSerializer,
    PaymentMethodSerializer,
    PaymentMethodDefaultSerializer,
)
from taybat_backend.typing import get_authenticated_user

class PaymentMethodListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsCustomer]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self) -> QuerySet[PaymentMethod]:
        user = get_authenticated_user(self.request)
        return PaymentMethod.objects.filter(user=user).order_by("-created_at")

    @transaction.atomic
    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        user = get_authenticated_user(self.request)
        pm: PaymentMethod = serializer.save(user=user)
        if pm.is_default:
            PaymentMethod.objects.filter(user=user).exclude(id=pm.pk).update(is_default=False)


class PaymentMethodUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCustomer]
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    def get_queryset(self) -> QuerySet[PaymentMethod]:
        user = get_authenticated_user(self.request)
        return PaymentMethod.objects.filter(user=user)

    @transaction.atomic
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        pm = self.get_object()
        s = PaymentMethodDefaultSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        make_default = s.validated_data["is_default"]

        if make_default:
            user = get_authenticated_user(request)
            PaymentMethod.objects.filter(user=user).update(is_default=False)
            pm.is_default = True
            pm.save(update_fields=["is_default"])
        else:
            pm.is_default = False
            pm.save(update_fields=["is_default"])

        return Response(PaymentMethodSerializer(pm).data)
