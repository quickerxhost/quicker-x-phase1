from django.contrib import admin

from apps.devices.models import RefreshToken, UserDevice


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ["user", "device_type", "device_id", "is_trusted", "last_active_at"]
    search_fields = ["user__phone_number", "device_id"]
    list_filter = ["device_type", "is_trusted"]


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "device", "jti", "is_revoked", "expires_at"]
    search_fields = ["user__phone_number", "jti"]
    list_filter = ["is_revoked"]
