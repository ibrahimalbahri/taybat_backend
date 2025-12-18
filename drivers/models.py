from django.db import models
from django.conf import settings


class DriverStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class VehicleType(models.TextChoices):
    BIKE = "BIKE", "Bike"
    MOTOR = "MOTOR", "Motorcycle"
    CAR = "CAR", "Car"
    VAN = "VAN", "Van"


class DriverProfile(models.Model):
    """
    Operational profile for drivers.
    Exists only for users with role=DRIVER.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_profile",
    )

    status = models.CharField(
        max_length=20,
        choices=DriverStatus.choices,
        default=DriverStatus.PENDING,
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
    )

    accepts_food = models.BooleanField(default=False)
    accepts_shipping = models.BooleanField(default=False)
    accepts_taxi = models.BooleanField(default=False)

    is_online = models.BooleanField(
        default=False,
        help_text="Whether the driver is currently online and available for orders",
    )

    driving_license = models.FileField(
        upload_to="drivers/licenses/",
        null=True,
        blank=True,
    )

    id_document = models.FileField(
        upload_to="drivers/ids/",
        null=True,
        blank=True,
    )

    other_documents = models.FileField(
        upload_to="drivers/other/",
        null=True,
        blank=True,
    )

    earnings_last_month = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cached value for quick access",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Driver Profile"
        verbose_name_plural = "Driver Profiles"

    def __str__(self) -> str:
        return f"DriverProfile({self.user.email})"
