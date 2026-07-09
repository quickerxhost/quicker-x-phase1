from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class LoginHistory(BaseModel):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        LOCKED = "LOCKED", "Locked"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_history",
        null=True, blank=True,
    )
    identifier_attempted = models.CharField(
        max_length=255, help_text="Phone number or email used for this login attempt."
    )

    status = models.CharField(max_length=10, choices=Status.choices, db_index=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "login_history"
        verbose_name = "Login History"
        verbose_name_plural = "Login History"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.identifier_attempted} - {self.status} @ {self.created_at}"
