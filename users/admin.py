from __future__ import annotations

from django.contrib import admin

from .models import CustomerProfile, SellerProfile, User, Address, DriverProfile


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

    @admin.display(description="Earnings Last Month")
    def earnings_last_month(self, obj: DriverProfile) -> float:
        return obj.earnings_last_month
    
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_sales",
        "created_at",
    )
    search_fields = ("user__email", "store_name")

    @admin.display(description="Total Sales")
    def total_sales(self, obj: SellerProfile) -> float:
        return sum(order.total_amount for order in obj.orders.all())
    
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_orders",
        "created_at",
    )
    search_fields = ("user__email",)

    @admin.display(description="Total Orders")
    def total_orders(self, obj: CustomerProfile) -> int:
        return obj.orders.count()
