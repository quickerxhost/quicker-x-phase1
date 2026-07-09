from rest_framework import serializers

from apps.audit.models import LoginHistory
from apps.users.models import User


class AdminUserListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "phone_number", "full_name", "account_type",
            "is_active", "is_email_verified", "is_phone_verified",
            "roles", "last_login", "created_at",
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return list(obj.active_roles)


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = [
            "id", "identifier_attempted", "status", "failure_reason",
            "ip_address", "user_agent", "device_id", "created_at",
        ]
        read_only_fields = fields
