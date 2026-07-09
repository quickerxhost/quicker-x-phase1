from django.contrib import admin

from apps.profiles.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "gender", "preferred_language", "marketing_opt_in"]
    search_fields = ["user__phone_number"]
