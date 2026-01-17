from django.contrib import admin
from .models import Restaurant, Category, Item, Coupon, CouponUsage


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "owner_user",
        "logo",
        "address",
        "lat",
        "lng",
        "phone",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("name", "phone", "owner_user__email", "owner_user__phone")
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "restaurant", "view_order")
    list_filter = ("restaurant",)
    search_fields = ("name", "restaurant__name")
    ordering = ("restaurant", "view_order", "name")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "restaurant",
        "category",
        "price",
        "image",
        "description",
        "ingredients",
        "customization_details",
        "is_available",
        "view_order",
        "created_at",
    )
    list_filter = ("restaurant", "category", "is_available")
    search_fields = ("name", "restaurant__name", "category__name")
    ordering = ("restaurant", "category", "view_order", "name")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "restaurant",
        "title",
        "description",
        "percentage",
        "min_price",
        "max_total_users",
        "max_per_customer",
        "start_date",
        "end_date",
        "is_active",
        "created_at",
    )
    list_filter = ("restaurant", "is_active")
    search_fields = ("code", "title", "restaurant__name")
    ordering = ("-created_at",)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "coupon", "user", "order", "created_at")
    list_filter = ("coupon", "created_at")
    search_fields = ("coupon__code", "user__email", "user__phone", "order__id")
    ordering = ("-created_at",)
