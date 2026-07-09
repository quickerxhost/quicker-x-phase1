from django.contrib import admin

from apps.shop_owner.models import ShopDocument, ShopImage, ShopOwnerRegistrationRequest


class ShopDocumentInline(admin.TabularInline):
    model = ShopDocument
    extra = 0
    readonly_fields = ["public_id", "secure_url", "document_type"]


class ShopImageInline(admin.TabularInline):
    model = ShopImage
    extra = 0
    readonly_fields = ["public_id", "secure_url", "image_type"]


@admin.register(ShopOwnerRegistrationRequest)
class ShopOwnerRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ["shop_name", "owner_email", "status", "city", "created_at"]
    list_filter = ["status", "business_type", "state"]
    search_fields = ["shop_name", "owner_email", "gstin", "pan_number"]
    inlines = [ShopDocumentInline, ShopImageInline]
    readonly_fields = ["reviewed_by", "reviewed_at"]
