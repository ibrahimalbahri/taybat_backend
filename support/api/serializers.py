from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from orders.models import Order
from sellers.models import Restaurant
from support.models import (
    SupportAttachment,
    SupportMessage,
    SupportRequesterRole,
    SupportTicket,
    SupportTicketStatus,
)
from users.models import User


class SupportAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAttachment
        fields = ["id", "file_url", "mime_type", "created_at"]
        read_only_fields = ["id", "created_at"]


class SupportMessageSerializer(serializers.ModelSerializer):
    attachments = SupportAttachmentSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = SupportMessage
        fields = ["id", "author", "author_name", "author_role", "body", "created_at", "attachments"]
        read_only_fields = ["id", "author", "author_name", "author_role", "created_at", "attachments"]


class SupportAttachmentInputSerializer(serializers.Serializer):
    file_url = serializers.URLField()
    mime_type = serializers.CharField(required=False, allow_blank=True)


class SupportMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    attachments = SupportAttachmentInputSerializer(many=True, required=False)

    def create(self, validated_data: dict[str, object]) -> SupportMessage:
        ticket: SupportTicket = self.context["ticket"]
        request = self.context["request"]
        author_role: str = self.context["author_role"]
        attachments = validated_data.pop("attachments", [])

        message = SupportMessage.objects.create(
            ticket=ticket,
            author=request.user,
            author_role=author_role,
            **validated_data,
        )

        for attachment in attachments:
            SupportAttachment.objects.create(message=message, **attachment)

        ticket.last_activity_at = timezone.now()
        ticket.save(update_fields=["last_activity_at"])
        return message


class SupportTicketListSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.name", read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "subject",
            "category",
            "priority",
            "status",
            "requester",
            "requester_name",
            "order",
            "restaurant",
            "driver",
            "assigned_to",
            "created_at",
            "updated_at",
            "last_activity_at",
            "closed_at",
        ]
        read_only_fields = fields


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.name", read_only=True)
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "subject",
            "category",
            "priority",
            "status",
            "requester",
            "requester_name",
            "order",
            "restaurant",
            "driver",
            "assigned_to",
            "assigned_to_name",
            "created_at",
            "updated_at",
            "last_activity_at",
            "closed_at",
            "messages",
        ]
        read_only_fields = fields


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(required=False, allow_null=True)
    restaurant_id = serializers.IntegerField(required=False, allow_null=True)
    driver_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = SupportTicket
        fields = [
            "subject",
            "category",
            "priority",
            "order_id",
            "restaurant_id",
            "driver_id",
        ]

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        request = self.context["request"]
        requester_role = self.context["requester_role"]
        order_id = attrs.get("order_id")
        restaurant_id = attrs.get("restaurant_id")

        order = None
        restaurant = None
        if order_id:
            order = Order.objects.select_related("restaurant", "driver").filter(id=order_id).first()
            if not order:
                raise serializers.ValidationError("order_id is invalid.")
            if order.restaurant:
                restaurant = order.restaurant

        if restaurant_id:
            restaurant = Restaurant.objects.filter(id=restaurant_id).first()
            if not restaurant:
                raise serializers.ValidationError("restaurant_id is invalid.")

        if order and restaurant and order.restaurant_id and order.restaurant_id != restaurant.id:
            raise serializers.ValidationError("order does not belong to this restaurant.")

        if requester_role == SupportRequesterRole.SELLER:
            if not restaurant:
                raise serializers.ValidationError("restaurant_id or order_id is required for sellers.")
            if restaurant.owner_user_id != request.user.id:
                raise serializers.ValidationError("restaurant does not belong to this seller.")

        driver_id = attrs.get("driver_id")
        if driver_id:
            driver = User.objects.filter(id=driver_id).first()
            if not driver or not driver.has_role("driver"):
                raise serializers.ValidationError("driver_id is invalid.")
            if requester_role == SupportRequesterRole.DRIVER and driver_id != request.user.id:
                raise serializers.ValidationError("driver_id must match the authenticated driver.")

        attrs["order"] = order
        attrs["restaurant"] = restaurant
        if order and order.driver_id and not attrs.get("driver_id"):
            attrs["driver_id"] = order.driver_id
        return attrs

    def create(self, validated_data: dict[str, object]) -> SupportTicket:
        request = self.context["request"]
        requester_role = self.context["requester_role"]

        order = validated_data.pop("order", None)
        restaurant = validated_data.pop("restaurant", None)
        order_id = validated_data.pop("order_id", None)
        restaurant_id = validated_data.pop("restaurant_id", None)
        driver_id = validated_data.pop("driver_id", None)

        if order is None and order_id:
            order = Order.objects.filter(id=order_id).first()
        if restaurant is None and restaurant_id:
            restaurant = Restaurant.objects.filter(id=restaurant_id).first()
        if requester_role == SupportRequesterRole.DRIVER:
            driver_id = request.user.id

        return SupportTicket.objects.create(
            requester=request.user,
            requester_role=requester_role,
            order=order,
            restaurant=restaurant,
            driver_id=driver_id,
            **validated_data,
        )


class SupportTicketAdminUpdateSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = SupportTicket
        fields = ["status", "priority", "assigned_to_id"]

    def validate_assigned_to_id(self, value: int | None) -> int | None:
        if value is None:
            return value
        user = User.objects.filter(id=value).first()
        if not user:
            raise serializers.ValidationError("assigned_to_id is invalid.")
        if not (user.is_superuser or user.has_role("admin")):
            raise serializers.ValidationError("assigned user must be admin/staff.")
        return value

    def update(self, instance: SupportTicket, validated_data: dict[str, object]) -> SupportTicket:
        status = validated_data.get("status")
        assigned_to_id = validated_data.pop("assigned_to_id", None)
        if assigned_to_id is not None:
            instance.assigned_to_id = assigned_to_id
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if status in {SupportTicketStatus.RESOLVED, SupportTicketStatus.CLOSED}:
            instance.closed_at = timezone.now()
        instance.save()
        return instance
