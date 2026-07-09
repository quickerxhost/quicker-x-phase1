from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class OTPVerification(BaseModel):
    class Purpose(models.TextChoices):
        REGISTRATION = "REGISTRATION", "Registration"
        LOGIN = "LOGIN", "Login"
        FORGOT_PASSWORD = "FORGOT_PASSWORD", "Forgot Password"
        PHONE_VERIFICATION = "PHONE_VERIFICATION", "Phone Verification"
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Email Verification"

    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp_verifications",
        null=True, blank=True,
    )
    # Supports pre-registration OTP (user not yet created) by target identifier.
    target = models.CharField(max_length=255, db_index=True)  # email or phone number

    code_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=30, choices=Purpose.choices, db_index=True)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.EMAIL)

    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otp_verifications"
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
        indexes = [
            models.Index(fields=["target", "purpose", "is_used"]),
        ]

    def __str__(self):
        return f"OTP<{self.target}:{self.purpose}>"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_exhausted(self):
        return self.attempts >= self.max_attempts
