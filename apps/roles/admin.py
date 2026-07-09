from django.contrib import admin

from apps.roles.models import Permission, Role, RolePermission, UserRole


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "is_active", "created_at"]
    search_fields = ["name"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "module", "is_active"]
    search_fields = ["code", "module"]
    list_filter = ["module"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission", "is_active"]
    list_filter = ["role"]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "is_active", "created_at"]
    list_filter = ["role"]
    search_fields = ["user__phone_number"]
