from __future__ import annotations

from typing import Optional, Tuple

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class Role(models.Model):
    name = models.CharField(max_length=32, unique=True, db_index=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        "users.Role",
        on_delete=models.CASCADE,
        related_name="role_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role"),
        ]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return f"UserRole(user={self.user_id}, role={self.role_id})"


class UserManager(BaseUserManager["User"]):
    """
    Custom user manager that uses email as the unique identifier.
    """

    def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields: object,
    ) -> "User":
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # Password handling is kept minimal; full auth logic can be added later.
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def get_or_create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields: object,
    ) -> Tuple["User", bool]:
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        try:
            return self.get(email=email), False
        except self.model.DoesNotExist:
            user = self.model(email=email, **extra_fields)
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save(using=self._db)
            return user, True

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields: object,
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(email, password, **extra_fields)
        user.add_role("admin")
        AdminProfile.objects.get_or_create(user=user)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using a unified schema.

    Authentication logic (views, serializers, tokens) is intentionally omitted for now.
    """

    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, unique=True, db_index=True) # TODO: Add phone number validation + format validation
    otp_code_hash = models.CharField(max_length=128, null=True, blank=True)
    otp_code_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Minimal Django auth flags (no extra auth logic yet)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    roles = models.ManyToManyField(
        "users.Role",
        through="users.UserRole",
        related_name="users",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def has_role(self, name: str) -> bool:
        return self.roles.filter(name=name.lower()).exists()

    def add_role(self, name: str) -> None:
        role, _ = Role.objects.get_or_create(name=name.lower())
        UserRole.objects.get_or_create(user=self, role=role)

    def remove_role(self, name: str) -> None:
        try:
            role = Role.objects.get(name=name.lower())
        except Role.DoesNotExist:
            return
        UserRole.objects.filter(user=self, role=role).delete()

    @property
    def is_customer_role(self) -> bool:
        return self.has_role("customer")

    @property
    def is_driver_role(self) -> bool:
        return self.has_role("driver")

    @property
    def is_seller_role(self) -> bool:
        return self.has_role("seller")

    @property
    def is_admin_role(self) -> bool:
        return self.has_role("admin")


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
    Exists only for users with the driver role.
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


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self) -> str:
        return f"CustomerProfile(user={self.user_id})"


class SellerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Seller Profile"
        verbose_name_plural = "Seller Profiles"

    def __str__(self) -> str:
        return f"SellerProfile(user={self.user_id})"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"

    def __str__(self) -> str:
        return f"AdminProfile(user={self.user_id})"


class Address(models.Model):
    """
    A saved address belonging to a user.
    Used for order pickup and dropoff.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    label = models.CharField(
        max_length=50,
        help_text="e.g. home, work, office"
    )

    lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude"
    )

    lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude"
    )

    full_address = models.TextField()
    street_name = models.CharField(max_length=255, null=True, blank=True)
    house_number = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self) -> str:
        return f"{self.label} - {self.full_address}"
