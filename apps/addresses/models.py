from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Address(BaseModel):
    class AddressType(models.TextChoices):
        HOME = "HOME", "Home"
        WORK = "WORK", "Work"
        SHOP = "SHOP", "Shop"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses"
    )

    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.HOME)
    label = models.CharField(max_length=100, blank=True)

    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, db_index=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "addresses"
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city", "state"]),
        ]

    def __str__(self):
        return f"{self.line1}, {self.city} ({self.address_type})"
