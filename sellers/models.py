from __future__ import annotations

from django.db import models
from django.conf import settings


class RestaurantStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class Restaurant(models.Model):
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_restaurants",
        help_text="User who owns the restaurant.",
    )

    name = models.CharField(max_length=255)

    logo = models.URLField(null=True, blank=True)
    address = models.TextField()
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)

    phone = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=RestaurantStatus.choices,
        default=RestaurantStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    name = models.CharField(max_length=100)
    view_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ("restaurant", "name")
        indexes = [
            models.Index(fields=["restaurant", "view_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.restaurant.name} - {self.name}"


class Item(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="items",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="items",
    )

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    image = models.URLField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    ingredients = models.TextField(null=True, blank=True)

    customization_details = models.JSONField(null=True, blank=True)

    view_order = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        unique_together = ("restaurant", "category", "name")
        indexes = [
            models.Index(fields=["restaurant", "category", "view_order"]),
            models.Index(fields=["restaurant", "is_available"]),
        ]

    def __str__(self) -> str:
        return f"{self.restaurant.name} - {self.name}"

class Coupon(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="coupons",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    code = models.CharField(max_length=50, db_index=True)

    percentage = models.PositiveIntegerField(help_text="Discount percentage (0-100)")

    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    max_total_users = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of unique users allowed to use this coupon",
    )

    max_per_customer = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum uses per customer",
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        unique_together = ("restaurant", "code")
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["restaurant", "code"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.restaurant.name} - {self.code}"


class CouponUsage(models.Model):
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
        help_text="Order that used this coupon (nullable for audit or pre-checkout reservations).",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coupon Usage"
        verbose_name_plural = "Coupon Usages"
        indexes = [
            models.Index(fields=["coupon", "user", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_coupon_usage_per_order"),
        ]

    def __str__(self) -> str:
        return f"CouponUsage(coupon={self.coupon_id}, user={self.user_id})"
