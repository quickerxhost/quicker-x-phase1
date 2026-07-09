import re

from django.core.exceptions import ValidationError


def validate_phone_number(value: str):
    pattern = r"^\+?[1-9]\d{7,14}$"
    if not re.match(pattern, value):
        raise ValidationError("Enter a valid phone number in E.164 format, e.g. +919876543210.")


def validate_strong_password(value: str):
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", value):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()\-_=+{};:,<.>]", value):
        raise ValidationError("Password must contain at least one special character.")


def validate_otp_code(value: str):
    if not re.match(r"^\d{4}$", value):
        raise ValidationError("OTP must be a 4-digit numeric code.")
