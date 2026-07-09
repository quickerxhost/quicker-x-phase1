from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["phone_number", "full_name", "account_type", "is_active", "is_staff", "created_at"]
    list_filter = ["account_type", "is_active", "is_staff", "is_phone_verified"]
    search_fields = ["phone_number", "full_name", "email"]
    readonly_fields = ["id", "created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal Info", {"fields": ("full_name", "email")}),
        (
            "Status & Role",
            {"fields": ("account_type", "is_active", "is_email_verified", "is_phone_verified")},
        ),
        (
            "Permissions",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "full_name", "account_type", "password1", "password2"),
            },
        ),
    )
