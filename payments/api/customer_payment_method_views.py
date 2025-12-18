# payments/api/customer_payment_method_views.py
from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.response import Response

from payments.models import PaymentMethod
from users.permissions import IsCustomer
from .customer_payment_method_serializers import (
    PaymentMethodCreateSerializer,
    PaymentMethodSerializer,
    PaymentMethodDefaultSerializer,
)

class PaymentMethodListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsCustomer]
    serializer_class = PaymentMethodSerializer

    def get_queryset(self): # type: ignore
        return PaymentMethod.objects.filter(user=self.request.user).order_by("-created_at")

    @transaction.atomic
    def perform_create(self, serializer):
        pm: PaymentMethod = serializer.save(user=self.request.user)
        if pm.is_default:
            PaymentMethod.objects.filter(user=self.request.user).exclude(id=pm.pk).update(is_default=False)


class PaymentMethodUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCustomer]
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer

    def get_queryset(self): # type: ignore
        return PaymentMethod.objects.filter(user=self.request.user)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        pm = self.get_object()
        s = PaymentMethodDefaultSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        make_default = s.validated_data["is_default"]

        if make_default:
            PaymentMethod.objects.filter(user=request.user).update(is_default=False)
            pm.is_default = True
            pm.save(update_fields=["is_default"])
        else:
            pm.is_default = False
            pm.save(update_fields=["is_default"])

        return Response(PaymentMethodSerializer(pm).data)
