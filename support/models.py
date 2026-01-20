from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from orders.models import Order
    from sellers.models import Restaurant
    from users.models import User


class SupportRequesterRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    SELLER = "SELLER", "Seller"
    DRIVER = "DRIVER", "Driver"


class SupportMessageAuthorRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    SELLER = "SELLER", "Seller"
    DRIVER = "DRIVER", "Driver"
    STAFF = "STAFF", "Staff"


class SupportTicketStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    WAITING_ON_CUSTOMER = "WAITING_ON_CUSTOMER", "Waiting on customer"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"


class SupportTicketPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class SupportTicketCategory(models.TextChoices):
    ORDER = "ORDER", "Order"
    PAYMENT = "PAYMENT", "Payment"
    DELIVERY = "DELIVERY", "Delivery"
    ACCOUNT = "ACCOUNT", "Account"
    OTHER = "OTHER", "Other"


class SupportTicket(models.Model):
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="support_tickets",
    )
    requester_role = models.CharField(max_length=20, choices=SupportRequesterRole.choices)

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    restaurant = models.ForeignKey(
        "sellers.Restaurant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_support_tickets",
    )

    subject = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=SupportTicketCategory.choices)
    priority = models.CharField(
        max_length=20,
        choices=SupportTicketPriority.choices,
        default=SupportTicketPriority.MEDIUM,
    )
    status = models.CharField(
        max_length=30,
        choices=SupportTicketStatus.choices,
        default=SupportTicketStatus.OPEN,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_tickets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    if TYPE_CHECKING:
        requester_user: User
        assigned_user: User
        order_record: Order
        restaurant_record: Restaurant
        messages: RelatedManager["SupportMessage"]

    class Meta:
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"
        indexes = [
            models.Index(fields=["status", "priority", "created_at"]),
            models.Index(fields=["requester", "created_at"]),
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["order"]),
            models.Index(fields=["restaurant"]),
        ]

    def __str__(self) -> str:
        return f"Ticket({self.id}) {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
    )
    author_role = models.CharField(max_length=20, choices=SupportMessageAuthorRole.choices)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    if TYPE_CHECKING:
        attachments: RelatedManager["SupportAttachment"]

    class Meta:
        verbose_name = "Support Message"
        verbose_name_plural = "Support Messages"
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"SupportMessage(ticket={self.ticket_id}, author={self.author_id})"


class SupportAttachment(models.Model):
    message = models.ForeignKey(
        SupportMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file_url = models.URLField()
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Support Attachment"
        verbose_name_plural = "Support Attachments"
        indexes = [
            models.Index(fields=["message"]),
        ]

    def __str__(self) -> str:
        return f"SupportAttachment(message={self.message_id})"
