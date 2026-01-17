from django.contrib import admin

from .models import PaymentMethod, Transaction


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "provider",
        "token",
        "brand",
        "last4",
        "exp_month",
        "exp_year",
        "is_default",
        "created_at",
    )
    list_filter = ("provider", "is_default", "created_at")
    search_fields = ("user__email", "user__phone", "token", "brand", "last4")
    ordering = ("-created_at",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "order",
        "provider",
        "provider_ref",
        "type",
        "status",
        "amount",
        "currency",
        "idempotency_key",
        "metadata",
        "created_at",
    )
    list_filter = ("provider", "type", "status", "currency", "created_at")
    search_fields = ("user__email", "user__phone", "order__id", "provider_ref", "idempotency_key")
    ordering = ("-created_at",)
