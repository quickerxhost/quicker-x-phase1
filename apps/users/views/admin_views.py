from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from rest_framework import filters, generics, views
from rest_framework.generics import get_object_or_404

from apps.audit.models import LoginHistory
from apps.core.exceptions import ApplicationError
from apps.core.permissions import IsAdminOrSuperAdmin
from apps.core.responses import success_response
from apps.devices.models import RefreshToken
from apps.users.models import User
from apps.users.serializers_admin import (
    AdminUserListSerializer,
    LoginHistorySerializer,
)


class AdminUserListView(generics.ListAPIView):
    """GET /api/v1/admin/users/"""

    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdminOrSuperAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["created_at", "full_name"]
    queryset = User.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        account_type = self.request.query_params.get("account_type")
        if account_type:
            qs = qs.filter(account_type=account_type)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Users retrieved successfully.")


class AdminUserActivateView(views.APIView):
    """PATCH /api/v1/admin/users/{id}/activate/"""

    permission_classes = [IsAdminOrSuperAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.updated_by = request.user
        user.save(update_fields=["is_active", "updated_by", "updated_at"])
        return success_response(message="User activated successfully.")


class AdminUserDeactivateView(views.APIView):
    """PATCH /api/v1/admin/users/{id}/deactivate/"""

    permission_classes = [IsAdminOrSuperAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.updated_by = request.user
        user.save(update_fields=["is_active", "updated_by", "updated_at"])

        # Force logout everywhere.
        RefreshToken.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

        return success_response(message="User deactivated successfully.")


class AdminUserDeleteView(views.APIView):
    """DELETE /api/v1/admin/users/{id}/ — soft delete only."""

    permission_classes = [IsAdminOrSuperAdmin]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            raise ApplicationError("Super admin accounts cannot be deleted.", status_code=403)

        user.soft_delete(actor=request.user)
        RefreshToken.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

        return success_response(message="User deleted successfully.")


class AdminUserResetPasswordView(views.APIView):
    """
    POST /api/v1/admin/users/{id}/reset-password/

    Admin-triggered reset: generates a temporary password and (in a real
    deployment) emails it to the user, forcing a change on next login.
    """

    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        temp_password = get_random_string(12)
        user.password = make_password(temp_password)
        user.save(update_fields=["password"])

        RefreshToken.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

        # TODO (Phase 2): deliver temp_password via email/SMS instead of API response.
        return success_response(
            data={"temporary_password": temp_password},
            message="Password reset. Share the temporary password with the user securely.",
        )


class AdminLoginHistoryView(generics.ListAPIView):
    """GET /api/v1/admin/users/{id}/login-history/"""

    serializer_class = LoginHistorySerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def get_queryset(self):
        return LoginHistory.objects.filter(user_id=self.kwargs["pk"])

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Login history retrieved successfully.")
