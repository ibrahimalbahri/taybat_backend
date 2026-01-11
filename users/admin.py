from __future__ import annotations

from django.contrib import admin

from .models import User, Address, DriverProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "roles_list", "is_verified", "is_staff", "created_at")
    list_filter = ("roles", "is_verified", "is_staff")
    search_fields = ("email", "phone", "name")
    ordering = ("-created_at",)

    @admin.display(description="Roles")
    def roles_list(self, obj: User) -> str:
        return ", ".join(obj.roles.values_list("name", flat=True))


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "full_address", "created_at")
    search_fields = ("full_address",)
    list_filter = ("label",)


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
