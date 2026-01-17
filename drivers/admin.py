from django.contrib import admin

from drivers.models import DriverLocation, DriverVerification


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "driver", "lat", "lng", "heading", "speed", "updated_at")
    search_fields = ("driver__id", "driver__email", "driver__phone")


@admin.register(DriverVerification)
class DriverVerificationAdmin(admin.ModelAdmin):
    list_display = ("id", "admin", "driver", "status", "notes", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("admin__email", "admin__phone", "driver__email", "driver__phone")
    ordering = ("-created_at",)
