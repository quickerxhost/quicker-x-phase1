from django.utils import timezone
from rest_framework import generics, permissions, status, views
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken

from apps.core.exceptions import ApplicationError
from apps.core.responses import success_response
from apps.devices.models import RefreshToken
from apps.otp.models import OTPVerification
from apps.otp.services import generate_and_send_otp, verify_otp
from apps.users.serializers import (
    ChangePasswordSerializer,
    CustomerRegistrationSerializer,
    FirebaseLoginSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenRequestSerializer,
    RequestLoginOtpSerializer,
    ResetPasswordSerializer,
    VerifyLoginOtpSerializer,
    VerifyOTPSerializer,
    VerifyRegistrationOtpSerializer,
)
from apps.users.services.auth_service import (
    authenticate_and_issue_tokens,
    authenticate_via_firebase,
    register_customer,
    request_login_otp,
    reset_password,
    verify_login_otp_and_login,
    verify_registration_otp_and_login,
)


class CustomerRegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/"""

    serializer_class = CustomerRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        register_customer(user)
        return success_response(
            data={"id": str(user.id), "phone_number": user.phone_number},
            message="Registration successful. Please verify your mobile number with the OTP sent to you.",
            status_code=201,
        )


class VerifyRegistrationOtpView(views.APIView):
    """
    POST /api/v1/auth/verify-registration-otp/

    Step 2 of OTP-only registration: verify the code sent to phone_number,
    activate the account, and log the user straight in (returns JWT pair).
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request):
        serializer = VerifyRegistrationOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, refresh = verify_registration_otp_and_login(
            request,
            phone_number=data["phone_number"],
            otp_code=data["otp"],
            device_id=data.get("device_id"),
            device_type=data.get("device_type"),
            fcm_token=data.get("fcm_token"),
        )

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "phone_number": user.phone_number,
                    "full_name": user.full_name,
                    "account_type": user.account_type,
                    "roles": list(user.active_roles),
                },
            },
            message="Mobile number verified. Registration complete.",
        )


class RequestLoginOtpView(views.APIView):
    """
    POST /api/v1/auth/request-login-otp/

    Step 1 of OTP-only login: sends an OTP to phone_number if a verified
    account exists. Always returns success either way (doesn't leak which
    numbers are registered), matching ForgotPasswordView's pattern.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request):
        serializer = RequestLoginOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_login_otp(serializer.validated_data["phone_number"])
        return success_response(message="If this mobile number is registered, an OTP has been sent.")


class VerifyLoginOtpView(views.APIView):
    """
    POST /api/v1/auth/verify-login-otp/

    Step 2 of OTP-only login: verify the code and issue the JWT pair.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = VerifyLoginOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, refresh = verify_login_otp_and_login(
            request,
            phone_number=data["phone_number"],
            otp_code=data["otp"],
            device_id=data.get("device_id"),
            device_type=data.get("device_type"),
            fcm_token=data.get("fcm_token"),
        )

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "phone_number": user.phone_number,
                    "full_name": user.full_name,
                    "account_type": user.account_type,
                    "roles": list(user.active_roles),
                },
            },
            message="Login successful.",
        )


class FirebaseLoginView(views.APIView):
    """
    POST /api/v1/auth/firebase-login/

    Body: {"id_token": "<Firebase ID token>", "full_name": "..."}
    (full_name only required the first time this phone number logs in)

    Replaces phone_number + password login: the client verifies the phone
    number via Firebase Phone Auth first, then exchanges the resulting
    Firebase ID token here for this backend's own JWT access/refresh pair.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = FirebaseLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, refresh, created = authenticate_via_firebase(
            request,
            id_token=data["id_token"],
            full_name=data.get("full_name"),
            device_id=data.get("device_id"),
            device_type=data.get("device_type"),
            fcm_token=data.get("fcm_token"),
        )

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "phone_number": user.phone_number,
                    "full_name": user.full_name,
                    "account_type": user.account_type,
                    "roles": list(user.active_roles),
                },
            },
            message="Account created and logged in." if created else "Login successful.",
            status_code=201 if created else 200,
        )


class LoginView(views.APIView):
    """POST /api/v1/auth/login/"""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, refresh = authenticate_and_issue_tokens(
            request,
            phone_number=data["phone_number"],
            password=data["password"],
            device_id=data.get("device_id"),
            device_type=data.get("device_type"),
            fcm_token=data.get("fcm_token"),
        )

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "phone_number": user.phone_number,
                    "full_name": user.full_name,
                    "account_type": user.account_type,
                    "roles": list(user.active_roles),
                },
            },
            message="Login successful.",
        )


class LogoutView(views.APIView):
    """POST /api/v1/auth/logout/ — blacklists the given refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = SimpleJWTRefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise ApplicationError("Invalid or already expired refresh token.", status_code=400)

        RefreshToken.objects.filter(jti=str(token["jti"])).update(
            is_revoked=True, revoked_at=timezone.now(), revoked_reason="Logout"
        )

        return success_response(message="Logged out successfully.")


class RefreshTokenView(views.APIView):
    """POST /api/v1/auth/refresh/ — rotates refresh token, issues new access token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            old_token = SimpleJWTRefreshToken(serializer.validated_data["refresh"])
            old_jti = str(old_token["jti"])

            record = RefreshToken.objects.filter(jti=old_jti).first()
            if record and record.is_revoked:
                raise ApplicationError("This refresh token has been revoked.", status_code=401)

            new_access = str(old_token.access_token)

            # ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION are enabled in
            # settings, so blacklisting the old token and minting a sibling
            # refresh token from the same user_id claim gives us rotation
            # without needing the full user object round-tripped here.
            new_refresh = SimpleJWTRefreshToken()
            new_refresh["user_id"] = old_token["user_id"]
            new_refresh["account_type"] = old_token.payload.get("account_type")
            old_token.blacklist()

            if record:
                RefreshToken.objects.create(
                    user_id=record.user_id,
                    device_id=record.device_id,
                    jti=str(new_refresh["jti"]),
                    issued_at=timezone.now(),
                    expires_at=timezone.now() + new_refresh.lifetime,
                )
                record.is_revoked = True
                record.revoked_at = timezone.now()
                record.revoked_reason = "Rotated"
                record.save(update_fields=["is_revoked", "revoked_at", "revoked_reason"])
        except TokenError:
            raise ApplicationError("Invalid or expired refresh token.", status_code=401)

        return success_response(
            data={"access": new_access, "refresh": str(new_refresh)},
            message="Token refreshed successfully.",
        )


class ForgotPasswordView(views.APIView):
    """POST /api/v1/auth/forgot-password/ — sends OTP via SMS to the registered mobile number."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]

        from apps.users.models import User

        if User.objects.filter(phone_number=phone_number).exists():
            generate_and_send_otp(
                target=phone_number,
                purpose=OTPVerification.Purpose.FORGOT_PASSWORD,
                channel=OTPVerification.Channel.SMS,
            )

        # Always return success to avoid leaking which numbers are registered.
        return success_response(message="If this mobile number is registered, an OTP has been sent.")


class ResetPasswordView(views.APIView):
    """POST /api/v1/auth/reset-password/"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reset_password(
            phone_number=data["phone_number"], otp_code=data["otp"], new_password=data["new_password"]
        )
        return success_response(message="Password reset successfully. Please log in again.")


class VerifyOTPView(views.APIView):
    """POST /api/v1/auth/verify-otp/"""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "otp"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        otp = verify_otp(target=data["target"], purpose=data["purpose"], code=data["otp"])

        if otp.purpose == OTPVerification.Purpose.PHONE_VERIFICATION and otp.user:
            otp.user.is_phone_verified = True
            otp.user.save(update_fields=["is_phone_verified"])

        return success_response(message="OTP verified successfully.")


class ChangePasswordView(views.APIView):
    """POST /api/v1/auth/change-password/ — authenticated password change."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        if not user.check_password(data["current_password"]):
            raise ApplicationError("Current password is incorrect.", status_code=400)

        user.set_password(data["new_password"])
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "password_changed_at"])

        return success_response(message="Password changed successfully.")
