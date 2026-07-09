from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import BaseModel

phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Enter a valid phone number in E.164 format, e.g. +919876543210.",
)


class UserManager(BaseUserManager):
    """
    Phone-number-first manager. Every mockup screen (Login, Register,
    Forgot Password, OTP) collects a mobile number and never an email,
    so `phone_number` is the USERNAME_FIELD. Email is kept but optional —
    useful later for receipts/notifications, never required at signup.
    """

    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("Users must have a phone number.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if extra_fields.get("email"):
            extra_fields["email"] = self.normalize_email(extra_fields["email"])
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("account_type", User.AccountType.SUPER_ADMIN)
        extra_fields.setdefault("is_phone_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Single authentication table for every actor in the system:
    Customer, Shop Owner, Admin, Super Admin.

    Role-specific data (profile, shop registration, etc.) lives in
    related tables — this table only owns identity + credentials.
    """

    class AccountType(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        SHOP_OWNER = "SHOP_OWNER", "Shop Owner"
        ADMIN = "ADMIN", "Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    phone_number = models.CharField(
        max_length=20, unique=True, db_index=True, validators=[phone_validator]
    )
    # Optional — no mockup screen collects it at signup. Kept for future
    # notifications/receipts; add a "verify email" flow later if needed.
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)

    full_name = models.CharField(max_length=150)

    account_type = models.CharField(
        max_length=20, choices=AccountType.choices, default=AccountType.CUSTOMER, db_index=True
    )

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)  # Django admin access (Admin/Super Admin only)

    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["account_type", "is_active"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.phone_number} ({self.account_type})"

    @property
    def active_roles(self):
        return self.user_roles.filter(is_active=True, is_deleted=False).values_list(
            "role__name", flat=True
        )
