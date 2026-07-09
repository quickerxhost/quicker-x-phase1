from django.contrib import admin

from apps.audit.models import LoginHistory


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ["identifier_attempted", "status", "ip_address", "created_at"]
    list_filter = ["status"]
    search_fields = ["identifier_attempted", "ip_address"]
    readonly_fields = [f.name for f in LoginHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
