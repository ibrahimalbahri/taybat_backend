from django.contrib import admin

from support.models import SupportTicket, SupportMessage, SupportAttachment


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "status", "priority", "requester", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("subject", "requester__name", "requester__phone")


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "author", "created_at")
    search_fields = ("ticket__id", "author__name", "author__phone")


@admin.register(SupportAttachment)
class SupportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "file_url", "created_at")
    search_fields = ("file_url",)
