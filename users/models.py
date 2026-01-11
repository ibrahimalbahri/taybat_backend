from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"
    DRIVER = "DRIVER", "Driver"
    SELLER = "SELLER", "Seller"
    ADMIN = "ADMIN", "Admin"


class UserManager(BaseUserManager["User"]):
    """
    Custom user manager that uses email as the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
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

    def get_or_create_user(self, email, password=None, **extra_fields):
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

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using a unified schema.

    Authentication logic (views, serializers, tokens) is intentionally omitted for now.
    """

    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, unique=True, db_index=True) # TODO: Add phone number validation + format validation
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
    )
    otp_code_hash = models.CharField(max_length=128, null=True, blank=True)
    otp_code_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Minimal Django auth flags (no extra auth logic yet)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


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
    street_name = models.CharField(max_length=255)
    house_number = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self) -> str:
        return f"{self.label} - {self.full_address}"
