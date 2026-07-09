from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.core.validators import validate_phone_number
from apps.users.models import User


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """
    OTP-only registration: Full Name + Mobile Number, nothing else.
    No password is collected anywhere in this flow — the account is
    activated purely by verifying the OTP sent to phone_number
    (see VerifyRegistrationOtpView). The User row is created with an
    unusable password (Django's standard "no password" state).
    """

    phone_number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        model = User
        fields = ["phone_number", "full_name"]

    def validate_phone_number(self, value):
        existing = User.objects.filter(phone_number=value).first()
        if existing and existing.is_phone_verified:
            raise serializers.ValidationError("An account with this mobile number already exists.")
        return value

    def create(self, validated_data):
        # Re-registration attempt with an unverified number: reuse the same
        # row (update full_name, resend OTP) instead of raising a duplicate
        # phone_number IntegrityError.
        existing = User.objects.filter(phone_number=validated_data["phone_number"]).first()
        if existing and not existing.is_phone_verified:
            existing.full_name = validated_data["full_name"]
            existing.save(update_fields=["full_name"])
            return existing

        return User.objects.create_user(
            account_type=User.AccountType.CUSTOMER,
            password=None,  # OTP-only account — no password is ever set.
            **validated_data,
        )


class RequestLoginOtpSerializer(serializers.Serializer):
    """OTP-only login, step 1: just the phone number."""

    phone_number = serializers.CharField(validators=[validate_phone_number])


class VerifyRegistrationOtpSerializer(serializers.Serializer):
    """OTP-only registration, step 2: verify the OTP and auto-login."""

    phone_number = serializers.CharField(validators=[validate_phone_number])
    otp = serializers.CharField(max_length=4, min_length=4)
    device_id = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=["ANDROID", "IOS", "WEB"], required=False, allow_null=True
    )
    fcm_token = serializers.CharField(required=False, allow_blank=True)


class VerifyLoginOtpSerializer(serializers.Serializer):
    """OTP-only login, step 2: verify the OTP and issue tokens."""

    phone_number = serializers.CharField(validators=[validate_phone_number])
    otp = serializers.CharField(max_length=4, min_length=4)
    device_id = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=["ANDROID", "IOS", "WEB"], required=False, allow_null=True
    )
    fcm_token = serializers.CharField(required=False, allow_blank=True)


class FirebaseLoginSerializer(serializers.Serializer):
    """
    Firebase Phone Auth is the source of truth for identity now — the client
    verifies the phone number via Firebase (which sends the OTP itself) and
    hands us the resulting ID token instead of a phone_number + password pair.

    full_name is only required the first time this phone number is seen
    (i.e. when we're creating the account); existing users can omit it.
    """

    id_token = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    device_id = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=["ANDROID", "IOS", "WEB"], required=False, allow_null=True
    )
    fcm_token = serializers.CharField(required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    """Matches the Login mockup: mobile number + password."""

    phone_number = serializers.CharField(validators=[validate_phone_number])
    password = serializers.CharField(write_only=True)
    device_id = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.ChoiceField(
        choices=["ANDROID", "IOS", "WEB"], required=False, allow_null=True
    )
    fcm_token = serializers.CharField(required=False, allow_blank=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Embeds account_type and roles into the JWT payload so client apps
    (Flutter/React) can branch on role without an extra API call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["account_type"] = user.account_type
        token["full_name"] = user.full_name
        token["roles"] = list(user.active_roles)
        return token


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    """Matches the Forgot Password mockup: mobile number only."""

    phone_number = serializers.CharField(validators=[validate_phone_number])


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_number])
    otp = serializers.CharField(max_length=4, min_length=4)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class VerifyOTPSerializer(serializers.Serializer):
    """
    `target` is a phone number for every flow driven by these mockups
    (registration verification, forgot-password). Kept generic (not
    renamed to phone_number) so the same endpoint can still serve an
    email-based purpose later (e.g. Shop Owner or Admin flows) without
    a breaking change.
    """

    target = serializers.CharField()
    purpose = serializers.CharField()
    otp = serializers.CharField(max_length=4, min_length=4)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
