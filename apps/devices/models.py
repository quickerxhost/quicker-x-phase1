from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class UserDevice(BaseModel):
    class DeviceType(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"
        WEB = "WEB", "Web"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices"
    )

    device_id = models.CharField(max_length=255, db_index=True)  # client-generated unique id
    device_type = models.CharField(max_length=10, choices=DeviceType.choices)
    device_name = models.CharField(max_length=150, blank=True)

    fcm_token = models.CharField(max_length=500, blank=True, null=True)
    app_version = models.CharField(max_length=20, blank=True)
    os_version = models.CharField(max_length=20, blank=True)

    is_trusted = models.BooleanField(default=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_devices"
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        constraints = [
            models.UniqueConstraint(fields=["user", "device_id"], name="uniq_user_device")
        ]
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"{self.user.phone_number} - {self.device_type}:{self.device_id}"


class RefreshToken(BaseModel):
    """
    Tracks issued refresh tokens per device for session management,
    forced logout, and "log out of all devices" support. Works
    alongside SimpleJWT's own blacklist app for token invalidation.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    device = models.ForeignKey(
        UserDevice, on_delete=models.CASCADE, related_name="refresh_tokens", null=True, blank=True
    )

    jti = models.CharField(max_length=255, unique=True, db_index=True)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "refresh_tokens"
        verbose_name = "Refresh Token"
        verbose_name_plural = "Refresh Tokens"
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
        ]

    def __str__(self):
        return f"RefreshToken<{self.user.phone_number}:{self.jti[:8]}>"
