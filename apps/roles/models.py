from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Role(BaseModel):
    class RoleName(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        SHOP_OWNER = "SHOP_OWNER", "Shop Owner"
        ADMIN = "ADMIN", "Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    name = models.CharField(max_length=50, unique=True, choices=RoleName.choices, db_index=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name


class Permission(BaseModel):
    """
    Fine-grained permission, e.g. 'shop_owner.approve', 'user.deactivate'.
    Distinct from Django's built-in auth Permission model.
    """

    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    module = models.CharField(max_length=50, db_index=True)  # e.g. "users", "shop_owner"

    class Meta:
        db_table = "permissions"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        indexes = [models.Index(fields=["module"])]

    def __str__(self):
        return self.code


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        db_table = "role_permissions"
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission")
        ]

    def __str__(self):
        return f"{self.role.name} -> {self.permission.code}"


class UserRole(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")

    class Meta:
        db_table = "user_roles"
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")
        ]
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"{self.user.phone_number} -> {self.role.name}"
