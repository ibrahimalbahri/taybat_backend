from django.contrib import admin
from .models import User, Address


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "role", "is_verified", "is_staff", "created_at")
    list_filter = ("role", "is_verified", "is_staff")
    search_fields = ("email", "phone", "name")
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "full_address", "created_at")
    search_fields = ("full_address",)
    list_filter = ("label",)
