from django.contrib import admin

from .models import LoyaltyPoint


@admin.register(LoyaltyPoint)
class LoyaltyPointAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "points",
        "source",
        "order",
        "note",
        "created_by",
        "created_at",
    )
    list_filter = ("source", "created_at")
    search_fields = ("user__email", "user__phone", "order__id", "created_by__email", "created_by__phone")
    ordering = ("-created_at",)
