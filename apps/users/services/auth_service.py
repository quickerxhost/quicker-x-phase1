from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken

from apps.audit.services import record_login_attempt
from apps.core.exceptions import ApplicationError
from apps.devices.models import RefreshToken, UserDevice
from apps.otp.models import OTPVerification
from apps.otp.services import generate_and_send_otp, verify_otp
from apps.users.models import User


def register_customer(user: User):
    """Kicks off phone verification OTP right after signup (SMS channel)."""
    generate_and_send_otp(
        target=user.phone_number,
        purpose=OTPVerification.Purpose.PHONE_VERIFICATION,
        channel=OTPVerification.Channel.SMS,
        user=user,
    )


def register_device(user, device_id, device_type, fcm_token):
    if not device_id:
        return None
    device, _ = UserDevice.objects.update_or_create(
        user=user,
        device_id=device_id,
        defaults={
            "device_type": device_type or UserDevice.DeviceType.WEB,
            "fcm_token": fcm_token or None,
            "last_active_at": timezone.now(),
            "updated_by": user,
        },
    )
    return device


def authenticate_and_issue_tokens(
    request, phone_number, password, device_id=None, device_type=None, fcm_token=None
):
    user = User.objects.filter(phone_number=phone_number).first()

    if user is None or not user.check_password(password):
        record_login_attempt(request, phone_number, "FAILED", failure_reason="Invalid credentials")
        raise ApplicationError("Invalid mobile number or password.", status_code=401)

    if not user.is_active or user.is_deleted:
        record_login_attempt(request, phone_number, "FAILED", user=user, failure_reason="Account inactive")
        raise ApplicationError("This account has been deactivated. Contact support.", status_code=403)

    device = register_device(user, device_id, device_type, fcm_token)

    refresh = SimpleJWTRefreshToken.for_user(user)
    refresh["account_type"] = user.account_type
    refresh["full_name"] = user.full_name
    refresh["roles"] = list(user.active_roles)

    RefreshToken.objects.create(
        user=user,
        device=device,
        jti=str(refresh["jti"]),
        issued_at=timezone.now(),
        expires_at=timezone.now() + refresh.lifetime,
        created_by=user,
    )

    user.last_login = timezone.now()
    user.last_login_ip = request.META.get("REMOTE_ADDR")
    user.save(update_fields=["last_login", "last_login_ip"])

    record_login_attempt(request, phone_number, "SUCCESS", user=user, device_id=device_id or "")

    return user, refresh


def authenticate_via_firebase(
    request, id_token, full_name=None, device_id=None, device_type=None, fcm_token=None
):
    """
    Verifies a Firebase Phone Auth ID token, then finds-or-creates the
    matching User (Firebase already confirmed the phone number via its own
    OTP flow, so no password/OTP check happens here) and issues our own
    JWT pair exactly like the password-based login flow does.
    """
    from apps.core.firebase import verify_firebase_id_token

    decoded = verify_firebase_id_token(id_token)
    phone_number = decoded.get("phone_number")

    if not phone_number:
        raise ApplicationError(
            "This Firebase account has no verified phone number.", status_code=400
        )

    user = User.objects.filter(phone_number=phone_number).first()
    created = False

    if user is None:
        if not full_name:
            raise ApplicationError(
                "full_name is required to create an account for this phone number.",
                status_code=400,
            )
        user = User.objects.create_user(
            phone_number=phone_number,
            password=None,  # Firebase is the identity provider; no local password.
            full_name=full_name,
            account_type=User.AccountType.CUSTOMER,
            is_phone_verified=True,
        )
        created = True
    elif not user.is_phone_verified:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

    if not user.is_active or user.is_deleted:
        record_login_attempt(
            request, phone_number, "FAILED", user=user, failure_reason="Account inactive"
        )
        raise ApplicationError("This account has been deactivated. Contact support.", status_code=403)

    device = register_device(user, device_id, device_type, fcm_token)

    refresh = SimpleJWTRefreshToken.for_user(user)
    refresh["account_type"] = user.account_type
    refresh["full_name"] = user.full_name
    refresh["roles"] = list(user.active_roles)

    RefreshToken.objects.create(
        user=user,
        device=device,
        jti=str(refresh["jti"]),
        issued_at=timezone.now(),
        expires_at=timezone.now() + refresh.lifetime,
        created_by=user,
    )

    user.last_login = timezone.now()
    user.last_login_ip = request.META.get("REMOTE_ADDR")
    user.save(update_fields=["last_login", "last_login_ip"])

    record_login_attempt(request, phone_number, "SUCCESS", user=user, device_id=device_id or "")

    return user, refresh, created


def _issue_tokens(request, user, device_id, device_type, fcm_token):
    """Shared token-issuance tail used by every OTP-based login path below."""
    device = register_device(user, device_id, device_type, fcm_token)

    refresh = SimpleJWTRefreshToken.for_user(user)
    refresh["account_type"] = user.account_type
    refresh["full_name"] = user.full_name
    refresh["roles"] = list(user.active_roles)

    RefreshToken.objects.create(
        user=user,
        device=device,
        jti=str(refresh["jti"]),
        issued_at=timezone.now(),
        expires_at=timezone.now() + refresh.lifetime,
        created_by=user,
    )

    user.last_login = timezone.now()
    user.last_login_ip = request.META.get("REMOTE_ADDR")
    user.save(update_fields=["last_login", "last_login_ip"])

    return refresh


def request_login_otp(phone_number: str):
    """
    OTP-only login, step 1. Always returns success regardless of whether
    the number is registered, to avoid leaking which numbers have accounts
    (same privacy pattern already used by ForgotPasswordView).
    """
    user = User.objects.filter(phone_number=phone_number, is_phone_verified=True).first()
    if user and user.is_active and not user.is_deleted:
        generate_and_send_otp(
            target=phone_number,
            purpose=OTPVerification.Purpose.LOGIN,
            channel=OTPVerification.Channel.SMS,
            user=user,
        )


def verify_registration_otp_and_login(
    request, phone_number, otp_code, device_id=None, device_type=None, fcm_token=None
):
    """OTP-only registration, step 2: verify the OTP, activate the account, log in."""
    verify_otp(target=phone_number, purpose=OTPVerification.Purpose.PHONE_VERIFICATION, code=otp_code)

    user = User.objects.filter(phone_number=phone_number).first()
    if user is None:
        raise ApplicationError("No pending registration found for this mobile number.", status_code=404)

    if not user.is_phone_verified:
        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

    refresh = _issue_tokens(request, user, device_id, device_type, fcm_token)
    record_login_attempt(request, phone_number, "SUCCESS", user=user, device_id=device_id or "")
    return user, refresh


def verify_login_otp_and_login(
    request, phone_number, otp_code, device_id=None, device_type=None, fcm_token=None
):
    """OTP-only login, step 2: verify the OTP and issue tokens."""
    user = User.objects.filter(phone_number=phone_number, is_phone_verified=True).first()
    if user is None:
        record_login_attempt(request, phone_number, "FAILED", failure_reason="No account found")
        raise ApplicationError("Invalid mobile number or OTP.", status_code=401)

    verify_otp(target=phone_number, purpose=OTPVerification.Purpose.LOGIN, code=otp_code)

    if not user.is_active or user.is_deleted:
        record_login_attempt(request, phone_number, "FAILED", user=user, failure_reason="Account inactive")
        raise ApplicationError("This account has been deactivated. Contact support.", status_code=403)

    refresh = _issue_tokens(request, user, device_id, device_type, fcm_token)
    record_login_attempt(request, phone_number, "SUCCESS", user=user, device_id=device_id or "")
    return user, refresh


def reset_password(phone_number: str, otp_code: str, new_password: str):
    from apps.otp.models import OTPVerification as OTPModel

    verify_otp(target=phone_number, purpose=OTPModel.Purpose.FORGOT_PASSWORD, code=otp_code)

    user = User.objects.filter(phone_number=phone_number).first()
    if user is None:
        raise ApplicationError("No account found for this mobile number.", status_code=404)

    user.set_password(new_password)
    user.password_changed_at = timezone.now()
    user.save(update_fields=["password", "password_changed_at"])

    # Force logout everywhere: revoke all outstanding refresh tokens.
    RefreshToken.objects.filter(user=user, is_revoked=False).update(
        is_revoked=True, revoked_at=timezone.now(), revoked_reason="Password reset"
    )
    return user
