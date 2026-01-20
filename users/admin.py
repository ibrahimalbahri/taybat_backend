from __future__ import annotations

from django.contrib import admin

from .models import CustomerProfile, OtpRequest, SellerProfile, User, Address, DriverProfile, Role, UserRole, AdminProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "name",
        "phone",
        "age",
        "roles_list",
        "is_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    list_filter = ("roles", "is_verified", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "phone", "name")
    ordering = ("-created_at",)

    @admin.display(description="Roles")
    def roles_list(self, obj: User) -> str:
        return ", ".join(obj.roles.values_list("name", flat=True))


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "label",
        "lat",
        "lng",
        "full_address",
        "street_name",
        "house_number",
        "city",
        "postal_code",
        "country",
        "created_at",
    )
    search_fields = ("full_address", "street_name", "city", "postal_code", "country")
    list_filter = ("label", "city", "country")


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "vehicle_type",
        "accepts_food",
        "accepts_shipping",
        "accepts_taxi",
        "is_online",
        "driving_license",
        "id_document",
        "other_documents",
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
        "id",
        "user",
        "total_sales",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__email", "store_name")

    @admin.display(description="Total Sales")
    def total_sales(self, obj: SellerProfile) -> float:
        return sum(order.total_amount for order in obj.orders.all())
    
@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "total_orders",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__email",)

    @admin.display(description="Total Orders")
    def total_orders(self, obj: CustomerProfile) -> int:
        return obj.orders.count()


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__email", "user__phone")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "created_at")
    search_fields = ("user__email", "user__phone", "role__name")
    list_filter = ("role",)

@admin.register(OtpRequest)
class OtpRequestAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code_hash', 'created_at')
    search_fields = ('phone', 'code_hash', 'created_at')
    list_filter = ('phone',)