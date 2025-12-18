from django.contrib import admin
from .models import (
    Order,
    OrderItem,
    ShippingPackage,
    OrderDriverSuggestion,
    OrderStatusHistory,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "timestamp")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_type",
        "status",
        "requested_vehicle_type",
        "requested_delivery_type",
        "customer",
        "driver",
        "restaurant",
        "total_amount",
        "tip",
        "delivery_fee",
        "created_at",
    )
    list_filter = ("order_type", "status", "restaurant")
    search_fields = ("id", "customer__email", "customer__phone", "driver__email", "driver__phone")
    ordering = ("-created_at",)
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(ShippingPackage)
class ShippingPackageAdmin(admin.ModelAdmin):
    list_display = ("order", "size", "weight", "content")
    search_fields = ("order__id",)


@admin.register(OrderDriverSuggestion)
class OrderDriverSuggestionAdmin(admin.ModelAdmin):
    list_display = ("order", "driver", "distance_at_time", "created_at")
    list_filter = ("created_at",)
    search_fields = ("order__id", "driver__email", "driver__phone")
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("order__id",)
    ordering = ("-timestamp",)
