from django.contrib import admin
from .models import (
    ManualOrder,
    Order,
    OrderDispatchState,
    OrderItem,
    ShippingPackage,
    OrderDriverSuggestion,
    OrderStatusHistory,
)
from .models_exports import Export


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
        "coupon",
        "subtotal_amount",
        "discount_amount",
        "total_amount",
        "tip",
        "delivery_fee",
        "pickup_address",
        "dropoff_address",
        "calculated_distance",
        "calculated_time",
        "is_manual",
        "created_at",
    )
    list_filter = ("order_type", "status", "restaurant")
    search_fields = ("id", "customer__email", "customer__phone", "driver__email", "driver__phone")
    ordering = ("-created_at",)
    inlines = [OrderItemInline, OrderStatusHistoryInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "item", "quantity", "customizations")
    search_fields = ("order__id", "item__name")
    ordering = ("-id",)


@admin.register(ShippingPackage)
class ShippingPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "size", "weight", "content")
    search_fields = ("order__id", "content")


@admin.register(OrderDriverSuggestion)
class OrderDriverSuggestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "driver",
        "status",
        "distance_at_time",
        "cycle",
        "notified_at",
        "expires_at",
        "responded_at",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order__id", "driver__email", "driver__phone")
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("order__id",)
    ordering = ("-timestamp",)

@admin.register(OrderDispatchState)
class OrderDispatchStateAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "is_active", "cycle", "last_dispatched_at", "next_retry_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("order__id",)
    ordering = ("-updated_at",)

@admin.register(ManualOrder)
class ManualOrderAdmin(admin.ModelAdmin):   
    list_display = ("id", "order", "staff_user", "scanned_form_data", "created_at")
    search_fields = ("order__id", "staff_user__email", "staff_user__phone")
    ordering = ("-created_at",) 


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    list_display = ("id", "admin", "file_path", "filter_params", "created_at")
    search_fields = ("admin__email", "admin__phone", "file_path")
    ordering = ("-created_at",)
