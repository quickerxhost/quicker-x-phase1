from django.contrib import admin

from apps.otp.models import OTPVerification


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ["target", "purpose", "channel", "is_used", "attempts", "expires_at", "created_at"]
    list_filter = ["purpose", "channel", "is_used"]
    search_fields = ["target"]
    readonly_fields = ["code_hash"]
