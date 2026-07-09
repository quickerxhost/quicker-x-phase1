from django.contrib import admin

from apps.addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "address_type", "city", "state", "is_default"]
    search_fields = ["user__phone_number", "city", "postal_code"]
    list_filter = ["address_type", "state"]
