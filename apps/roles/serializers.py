from rest_framework import serializers

from apps.roles.models import Permission, Role, RolePermission, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description", "module", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "is_active", "permissions", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_permissions(self, obj):
        codes = RolePermission.objects.filter(role=obj, is_active=True).values_list(
            "permission__code", flat=True
        )
        return list(codes)


class AssignRolePermissionSerializer(serializers.Serializer):
    role_id = serializers.UUIDField()
    permission_id = serializers.UUIDField()

    def validate(self, attrs):
        if not Role.objects.filter(id=attrs["role_id"]).exists():
            raise serializers.ValidationError({"role_id": "Role not found."})
        if not Permission.objects.filter(id=attrs["permission_id"]).exists():
            raise serializers.ValidationError({"permission_id": "Permission not found."})
        return attrs


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "user", "role", "role_name", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
