from __future__ import annotations

from django.db.models import QuerySet
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from support.api.serializers import (
    SupportMessageCreateSerializer,
    SupportMessageSerializer,
    SupportTicketAdminUpdateSerializer,
    SupportTicketCreateSerializer,
    SupportTicketDetailSerializer,
    SupportTicketListSerializer,
)
from support.models import SupportMessageAuthorRole, SupportRequesterRole, SupportTicket
from taybat_backend.typing import get_authenticated_user
from users.permissions import IsAdmin, IsCustomer, IsDriver, IsSeller


def _base_ticket_queryset() -> QuerySet[SupportTicket]:
    return SupportTicket.objects.select_related(
        "requester",
        "assigned_to",
        "order",
        "restaurant",
        "driver",
    )


def _customer_ticket_queryset(user) -> QuerySet[SupportTicket]:
    return _base_ticket_queryset().filter(requester=user)


def _driver_ticket_queryset(user) -> QuerySet[SupportTicket]:
    return _base_ticket_queryset().filter(requester=user)


def _seller_ticket_queryset(user) -> QuerySet[SupportTicket]:
    return _base_ticket_queryset().filter(
        Q(restaurant__owner_user=user) | Q(order__restaurant__owner_user=user)
    )


class BaseSupportTicketListCreateView(generics.ListCreateAPIView):
    requester_role: SupportRequesterRole

    @extend_schema(
        responses={200: SupportTicketListSerializer(many=True)},
        description="List support tickets available to the authenticated user.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=SupportTicketCreateSerializer,
        responses={201: SupportTicketDetailSerializer},
        description="Create a support ticket for the authenticated user.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method == "POST":
            return SupportTicketCreateSerializer
        return SupportTicketListSerializer

    def get_serializer_context(self) -> dict[str, object]:
        context = super().get_serializer_context()
        context["requester_role"] = self.requester_role
        return context

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        ticket = serializer.save()
        self.created_ticket = ticket

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().create(request, *args, **kwargs)
        if hasattr(self, "created_ticket"):
            response.data = SupportTicketDetailSerializer(self.created_ticket).data
        return response


class BaseSupportTicketDetailView(generics.RetrieveAPIView):
    serializer_class = SupportTicketDetailSerializer

    @extend_schema(
        responses={200: SupportTicketDetailSerializer},
        description="Retrieve a support ticket.",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[SupportTicket]:
        return _base_ticket_queryset().prefetch_related("messages__attachments")


class BaseSupportMessageCreateView(generics.CreateAPIView):
    serializer_class = SupportMessageCreateSerializer
    author_role: SupportMessageAuthorRole

    @extend_schema(
        request=SupportMessageCreateSerializer,
        responses={201: SupportMessageSerializer},
        description="Add a message to a support ticket.",
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)

    def get_ticket_queryset(self) -> QuerySet[SupportTicket]:
        return _base_ticket_queryset()

    def get_ticket(self) -> SupportTicket:
        return get_object_or_404(self.get_ticket_queryset(), pk=self.kwargs.get("pk"))

    def get_serializer_context(self) -> dict[str, object]:
        context = super().get_serializer_context()
        context["ticket"] = self.get_ticket()
        context["author_role"] = self.author_role
        return context

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        self.created_message = serializer.save()

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().create(request, *args, **kwargs)
        if hasattr(self, "created_message"):
            response.data = SupportMessageSerializer(self.created_message).data
        return response


class CustomerSupportTicketListCreateView(BaseSupportTicketListCreateView):
    permission_classes = [IsAuthenticated, IsCustomer]
    requester_role = SupportRequesterRole.CUSTOMER

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _customer_ticket_queryset(user).order_by("-created_at")


class CustomerSupportTicketDetailView(BaseSupportTicketDetailView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _customer_ticket_queryset(user).prefetch_related("messages__attachments")


class CustomerSupportMessageCreateView(BaseSupportMessageCreateView):
    permission_classes = [IsAuthenticated, IsCustomer]
    author_role = SupportMessageAuthorRole.CUSTOMER

    def get_ticket_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _customer_ticket_queryset(user)


class SellerSupportTicketListCreateView(BaseSupportTicketListCreateView):
    permission_classes = [IsAuthenticated, IsSeller]
    requester_role = SupportRequesterRole.SELLER

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _seller_ticket_queryset(user).order_by("-created_at")


class SellerSupportTicketDetailView(BaseSupportTicketDetailView):
    permission_classes = [IsAuthenticated, IsSeller]

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _seller_ticket_queryset(user).prefetch_related("messages__attachments")


class SellerSupportMessageCreateView(BaseSupportMessageCreateView):
    permission_classes = [IsAuthenticated, IsSeller]
    author_role = SupportMessageAuthorRole.SELLER

    def get_ticket_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _seller_ticket_queryset(user)


class DriverSupportTicketListCreateView(BaseSupportTicketListCreateView):
    permission_classes = [IsAuthenticated, IsDriver]
    requester_role = SupportRequesterRole.DRIVER

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _driver_ticket_queryset(user).order_by("-created_at")


class DriverSupportTicketDetailView(BaseSupportTicketDetailView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _driver_ticket_queryset(user).prefetch_related("messages__attachments")


class DriverSupportMessageCreateView(BaseSupportMessageCreateView):
    permission_classes = [IsAuthenticated, IsDriver]
    author_role = SupportMessageAuthorRole.DRIVER

    def get_ticket_queryset(self) -> QuerySet[SupportTicket]:
        user = get_authenticated_user(self.request)
        return _driver_ticket_queryset(user)


class AdminSupportTicketListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = SupportTicketListSerializer

    @extend_schema(
        responses={200: SupportTicketListSerializer(many=True)},
        description="List all support tickets (admin).",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[SupportTicket]:
        return _base_ticket_queryset().order_by("-created_at")


class AdminSupportTicketDetailUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @extend_schema(
        responses={200: SupportTicketDetailSerializer},
        description="Retrieve a support ticket (admin).",
    )
    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=SupportTicketAdminUpdateSerializer,
        responses={200: SupportTicketDetailSerializer},
        description="Update support ticket status/priority/assignment (admin).",
    )
    def patch(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().patch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[SupportTicket]:
        return _base_ticket_queryset().prefetch_related("messages__attachments")

    def get_serializer_class(self) -> type[serializers.BaseSerializer]:
        if self.request.method == "GET":
            return SupportTicketDetailSerializer
        return SupportTicketAdminUpdateSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        response = super().update(request, *args, **kwargs)
        response.data = SupportTicketDetailSerializer(self.get_object()).data
        return response


class AdminSupportMessageCreateView(BaseSupportMessageCreateView):
    permission_classes = [IsAuthenticated, IsAdmin]
    author_role = SupportMessageAuthorRole.STAFF

    def get_ticket_queryset(self) -> QuerySet[SupportTicket]:
        return _base_ticket_queryset()
