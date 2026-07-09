from rest_framework import viewsets
from rest_framework.decorators import action

from apps.core.permissions import IsAdminOrSuperAdmin
from apps.core.responses import success_response
from apps.roles.models import Permission, Role, RolePermission
from apps.roles.serializers import (
    AssignRolePermissionSerializer,
    PermissionSerializer,
    RoleSerializer,
)


class RoleViewSet(viewsets.ModelViewSet):
    """
    Admin-only role management.

    GET    /api/v1/roles/
    POST   /api/v1/roles/
    GET    /api/v1/roles/{id}/
    PATCH  /api/v1/roles/{id}/
    DELETE /api/v1/roles/{id}/            (soft delete)
    POST   /api/v1/roles/assign-permission/
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Roles retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success_response(data=response.data, message="Role retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return success_response(data=serializer.data, message="Role created successfully.", status_code=201)

    def perform_destroy(self, instance):
        instance.soft_delete(actor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="Role deleted successfully.")

    @action(detail=False, methods=["post"], url_path="assign-permission")
    def assign_permission(self, request):
        serializer = AssignRolePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role_permission, created = RolePermission.objects.get_or_create(
            role_id=serializer.validated_data["role_id"],
            permission_id=serializer.validated_data["permission_id"],
            defaults={"created_by": request.user},
        )
        message = "Permission assigned to role." if created else "Permission already assigned to role."
        return success_response(message=message, status_code=201 if created else 200)


class PermissionViewSet(viewsets.ModelViewSet):
    """
    Admin-only permission management.

    GET    /api/v1/roles/permissions/
    POST   /api/v1/roles/permissions/
    GET    /api/v1/roles/permissions/{id}/
    PATCH  /api/v1/roles/permissions/{id}/
    DELETE /api/v1/roles/permissions/{id}/
    """

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminOrSuperAdmin]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Permissions retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return success_response(
            data=serializer.data, message="Permission created successfully.", status_code=201
        )

    def perform_destroy(self, instance):
        instance.soft_delete(actor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="Permission deleted successfully.")
