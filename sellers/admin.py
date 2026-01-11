from django.contrib import admin
from .models import Restaurant, Category, Item, Coupon, CouponUsage


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_user", "status", "phone", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "owner_user__email", "owner_user__phone")
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "view_order")
    list_filter = ("restaurant",)
    search_fields = ("name", "restaurant__name")
    ordering = ("restaurant", "view_order", "name")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "is_available", "view_order")
    list_filter = ("restaurant", "category", "is_available")
    search_fields = ("name", "restaurant__name", "category__name")
    ordering = ("restaurant", "category", "view_order", "name")

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "restaurant",
        "percentage",
        "min_price",
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
    list_display = ("coupon", "user", "order", "created_at")
    list_filter = ("coupon", "created_at")
    search_fields = ("coupon__code", "user__email", "user__phone", "order__id")
    ordering = ("-created_at",)
