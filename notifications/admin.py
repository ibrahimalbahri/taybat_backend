from django.contrib import admin
from .models import Notification, DeviceToken
from django.utils.html import format_html
from django.utils.timezone import localtime

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "recipient",
        "is_read"
    )
    list_filter = ("is_read", "created_at", "recipient")
    search_fields = ("title", "message", "recipient__email", "recipient__phone")
    ordering = ("-created_at",)
    
@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "token",
        "device_type",
        "is_active"
    )
    list_filter = ("is_active", "device_type", "created_at", "last_seen_at")
    search_fields = ("token", "user__email", "user__phone")
    ordering = ("-created_at",) 