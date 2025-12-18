from django.db import models
from django.conf import settings


class OrderType(models.TextChoices):
    FOOD = "FOOD", "Food"
    SHIPPING = "SHIPPING", "Shipping"
    TAXI = "TAXI", "Taxi"


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SEARCHING_FOR_DRIVER = "SEARCHING_FOR_DRIVER", "Searching for driver"
    DRIVER_NOTIFICATION_SENT = "DRIVER_NOTIFICATION_SENT", "Driver notification sent"
    ACCEPTED = "ACCEPTED", "Accepted"
    ON_THE_WAY = "ON_THE_WAY", "On the way"
    DELIVERED = "DELIVERED", "Delivered"
    COMPLETED = "COMPLETED", "Completed"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"

class VehicleType(models.TextChoices):
    BIKE = "BIKE", "Bike"
    MOTOR = "MOTOR", "Motorcycle"
    CAR = "CAR", "Car"
    VAN = "VAN", "Van"

class Order(models.Model):
    """
    Unified Order model supporting food, shipping, and taxi.
    """

    order_type = models.CharField(max_length=20, choices=OrderType.choices)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_orders",
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_orders",
    )

    restaurant = models.ForeignKey(
        "restaurants.Restaurant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Food orders only; null for shipping/taxi",
    )

    status = models.CharField(
        max_length=40,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    subtotal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total before discounts (baseline for coupon calculation).",
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Discount applied (e.g. via coupon).",
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    coupon = models.ForeignKey(
        "restaurants.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    pickup_address = models.ForeignKey(
        "users.Address",
        on_delete=models.PROTECT,
        related_name="pickup_orders",
    )

    dropoff_address = models.ForeignKey(
        "users.Address",
        on_delete=models.PROTECT,
        related_name="dropoff_orders",
    )

    calculated_distance = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Distance in km (or your chosen unit) calculated by pricing engine",
    )

    calculated_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated time in seconds (or your chosen unit) calculated by pricing engine",
    )
    requested_vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=["order_type", "status", "created_at"]),
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["driver", "created_at"]),
            models.Index(fields=["restaurant", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order({self.id}) - {self.order_type} - {self.status}"


class OrderItem(models.Model):
    """
    Food order line items only.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    item = models.ForeignKey(
        "restaurants.Item",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    quantity = models.PositiveIntegerField(default=1)

    customizations = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self) -> str:
        return f"OrderItem(order={self.order_id}, item={self.item_id}, qty={self.quantity})"


class ShippingPackage(models.Model):
    """
    Shipping package details (shipping orders only).
    """

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="shipping_package",
    )

    size = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    content = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Shipping Package"
        verbose_name_plural = "Shipping Packages"

    def __str__(self) -> str:
        return f"ShippingPackage(order={self.order_id})"


class OrderDriverSuggestion(models.Model):
    """
    Stores the 5 closest drivers sent the order offer (per dispatch cycle).
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="driver_suggestions",
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="order_suggestions",
    )

    distance_at_time = models.DecimalField(max_digits=10, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Driver Suggestion"
        verbose_name_plural = "Order Driver Suggestions"
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["driver", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Suggestion(order={self.order_id}, driver={self.driver_id})"


class OrderStatusHistory(models.Model):
    """
    Immutable status transition history for audit + analytics.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    status = models.CharField(max_length=40, choices=OrderStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status History"
        indexes = [
            models.Index(fields=["order", "timestamp"]),
            models.Index(fields=["status", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"OrderStatusHistory(order={self.order_id}, status={self.status})"
