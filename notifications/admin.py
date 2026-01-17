from django.contrib import admin

from .models import Notification, DeviceToken

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "recipient",
        "body",
        "data",
        "is_read",
        "read_at",
        "created_at",
    )
    list_filter = ("is_read", "created_at", "recipient")
    search_fields = ("title", "body", "recipient__email", "recipient__phone")
    ordering = ("-created_at",)
    
@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "token",
        "device_type",
        "is_active",
        "created_at",
        "last_seen_at",
    )
    list_filter = ("is_active", "device_type", "created_at", "last_seen_at")
    search_fields = ("token", "user__email", "user__phone")
    ordering = ("-created_at",) 
