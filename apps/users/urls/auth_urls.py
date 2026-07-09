from django.urls import path

from apps.users.views.auth_views import (
    ChangePasswordView,
    CustomerRegisterView,
    FirebaseLoginView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    RequestLoginOtpView,
    ResetPasswordView,
    VerifyLoginOtpView,
    VerifyOTPView,
    VerifyRegistrationOtpView,
)

urlpatterns = [
    path("register/", CustomerRegisterView.as_view(), name="auth-register"),
    path(
        "verify-registration-otp/",
        VerifyRegistrationOtpView.as_view(),
        name="auth-verify-registration-otp",
    ),
    path("request-login-otp/", RequestLoginOtpView.as_view(), name="auth-request-login-otp"),
    path("verify-login-otp/", VerifyLoginOtpView.as_view(), name="auth-verify-login-otp"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("firebase-login/", FirebaseLoginView.as_view(), name="auth-firebase-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("verify-otp/", VerifyOTPView.as_view(), name="auth-verify-otp"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
]
