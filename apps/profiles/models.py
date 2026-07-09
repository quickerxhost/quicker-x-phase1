from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class UserProfile(BaseModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    avatar_public_id = models.CharField(max_length=255, blank=True, null=True)
    avatar_secure_url = models.URLField(blank=True, null=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)

    bio = models.CharField(max_length=500, blank=True)

    preferred_language = models.CharField(max_length=10, default="en")
    marketing_opt_in = models.BooleanField(default=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile<{self.user.phone_number}>"
