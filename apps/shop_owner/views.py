from django.utils import timezone
from rest_framework import generics, parsers, permissions, status, views
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import ListAPIView
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken

from apps.audit.services import record_login_attempt
from apps.core.exceptions import ApplicationError
from apps.core.permissions import IsAdminOrSuperAdmin
from apps.core.responses import success_response
from apps.shop_owner.models import ShopOwnerRegistrationRequest
from apps.shop_owner.serializers import (
    ShopOwnerLoginSerializer,
    ShopOwnerRegistrationRequestOutputSerializer,
    ShopOwnerRegistrationRequestSerializer,
    ShopOwnerRejectSerializer,
)
from apps.shop_owner.services.registration_service import approve_registration, reject_registration
from apps.users.models import User


class ShopOwnerRegisterRequestView(generics.CreateAPIView):
    """
    POST /api/v1/shop-owner/register-request/

    Accepts multipart/form-data: all shop + owner fields plus document/image
    files. Creates a User (SHOP_OWNER, login-gated) and a PENDING
    registration request for admin review.
    """

    serializer_class = ShopOwnerRegistrationRequestSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    throttle_scope = "register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registration = serializer.save()
        output = ShopOwnerRegistrationRequestOutputSerializer(registration)
        return success_response(
            data=output.data,
            message="Registration submitted. It is now pending admin approval.",
            status_code=201,
        )


class ShopOwnerLoginView(views.APIView):
    """
    POST /api/v1/shop-owner/login/

    Only succeeds if the linked registration request status is APPROVED.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = ShopOwnerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email, account_type=User.AccountType.SHOP_OWNER).first()

        if user is None or not user.check_password(password):
            record_login_attempt(request, email, "FAILED", failure_reason="Invalid credentials")
            raise AuthenticationFailed("Invalid email or password.")

        registration = getattr(user, "shop_owner_request", None)

        if registration is None:
            record_login_attempt(request, email, "FAILED", user=user, failure_reason="No registration request found")
            raise ApplicationError("No shop registration found for this account.", status_code=404)

        if registration.status == ShopOwnerRegistrationRequest.Status.PENDING:
            record_login_attempt(request, email, "FAILED", user=user, failure_reason="Registration pending")
            raise ApplicationError("Your registration is still pending admin approval.", status_code=403)

        if registration.status == ShopOwnerRegistrationRequest.Status.REJECTED:
            record_login_attempt(request, email, "FAILED", user=user, failure_reason="Registration rejected")
            raise ApplicationError(
                "Your registration was rejected.",
                errors={"rejection_reason": registration.rejection_reason},
                status_code=403,
            )

        if not user.is_active:
            record_login_attempt(request, email, "FAILED", user=user, failure_reason="Account inactive")
            raise ApplicationError("This account has been deactivated.", status_code=403)

        refresh = SimpleJWTRefreshToken.for_user(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        record_login_attempt(request, email, "SUCCESS", user=user)

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "account_type": user.account_type,
                    "shop_name": registration.shop_name,
                },
            },
            message="Login successful.",
        )


# ---------------------------------------------------------------------------
# Admin-facing shop owner approval workflow
# ---------------------------------------------------------------------------

class AdminPendingShopOwnerListView(ListAPIView):
    """GET /api/v1/admin/shop-owner/pending/"""

    serializer_class = ShopOwnerRegistrationRequestOutputSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        return ShopOwnerRegistrationRequest.objects.filter(
            status=ShopOwnerRegistrationRequest.Status.PENDING
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Pending shop owner requests retrieved.")


class AdminShopOwnerApproveView(views.APIView):
    """PATCH /api/v1/admin/shop-owner/{id}/approve/"""

    permission_classes = [IsAdminOrSuperAdmin]

    def patch(self, request, pk):
        registration = generics.get_object_or_404(ShopOwnerRegistrationRequest, pk=pk)
        registration = approve_registration(registration, admin_user=request.user)
        output = ShopOwnerRegistrationRequestOutputSerializer(registration)
        return success_response(data=output.data, message="Shop owner registration approved.")


class AdminShopOwnerRejectView(views.APIView):
    """PATCH /api/v1/admin/shop-owner/{id}/reject/"""

    permission_classes = [IsAdminOrSuperAdmin]

    def patch(self, request, pk):
        serializer = ShopOwnerRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        registration = generics.get_object_or_404(ShopOwnerRegistrationRequest, pk=pk)
        registration = reject_registration(
            registration, admin_user=request.user, reason=serializer.validated_data["reason"]
        )
        output = ShopOwnerRegistrationRequestOutputSerializer(registration)
        return success_response(data=output.data, message="Shop owner registration rejected.")
