from django.contrib import admin
from .models import DriverProfile


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "vehicle_type",
        "accepts_food",
        "accepts_shipping",
        "accepts_taxi",
        "earnings_last_month",
        "created_at",
    )
    list_filter = ("status", "vehicle_type", "accepts_food", "accepts_shipping", "accepts_taxi")
    search_fields = ("user__email", "user__phone")
