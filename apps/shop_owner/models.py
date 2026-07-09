from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class ShopOwnerRegistrationRequest(BaseModel):
    """
    Captures every field from the Shop Owner registration form.

    NOTE: field names below are a comprehensive best-practice superset
    for a marketplace shop-registration form (owner identity, business
    identity, statutory IDs, banking, address). Once the actual Flutter
    Shop Owner UI form is shared field-by-field, this model should be
    reconciled 1:1 against it — add/rename fields to match exactly,
    then regenerate the migration. Nothing here should be assumed final.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class BusinessType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual / Proprietorship"
        PARTNERSHIP = "PARTNERSHIP", "Partnership"
        PRIVATE_LIMITED = "PRIVATE_LIMITED", "Private Limited"
        LLP = "LLP", "LLP"
        OTHER = "OTHER", "Other"

    # Link to the auth account created for this shop owner (created at signup time,
    # inactive for login purposes until approved).
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shop_owner_request"
    )

    # --- Owner identity ---
    owner_full_name = models.CharField(max_length=150)
    owner_email = models.EmailField()
    owner_phone_number = models.CharField(max_length=20)
    owner_date_of_birth = models.DateField(null=True, blank=True)

    # --- Business identity ---
    shop_name = models.CharField(max_length=200, db_index=True)
    business_type = models.CharField(max_length=20, choices=BusinessType.choices)
    shop_category = models.CharField(max_length=100, blank=True)
    shop_description = models.TextField(blank=True)

    # --- Statutory / compliance ---
    gstin = models.CharField(max_length=15, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    fssai_license_number = models.CharField(max_length=30, blank=True, null=True)

    # --- Shop address ---
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- Banking (for payouts) ---
    bank_account_holder_name = models.CharField(max_length=150, blank=True)
    bank_account_number = models.CharField(max_length=30, blank=True)
    bank_ifsc_code = models.CharField(max_length=15, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)

    # --- Workflow ---
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_shop_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "shop_owner_registration_requests"
        verbose_name = "Shop Owner Registration Request"
        verbose_name_plural = "Shop Owner Registration Requests"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["shop_name"]),
        ]

    def __str__(self):
        return f"{self.shop_name} ({self.status})"


class CloudinaryAssetMixin(models.Model):
    """
    Shared Cloudinary metadata fields. Only metadata is stored in
    Postgres — the binary asset itself lives in Cloudinary.
    """

    public_id = models.CharField(max_length=255)
    secure_url = models.URLField()
    resource_type = models.CharField(max_length=20, default="image")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    bytes = models.PositiveIntegerField(null=True, blank=True)
    folder = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=50, blank=True)
    format = models.CharField(max_length=20, blank=True)

    class Meta:
        abstract = True


class ShopDocument(CloudinaryAssetMixin, BaseModel):
    class DocumentType(models.TextChoices):
        GST_CERTIFICATE = "GST_CERTIFICATE", "GST Certificate"
        PAN_CARD = "PAN_CARD", "PAN Card"
        FSSAI_LICENSE = "FSSAI_LICENSE", "FSSAI License"
        SHOP_LICENSE = "SHOP_LICENSE", "Shop License"
        IDENTITY_PROOF = "IDENTITY_PROOF", "Identity Proof"
        ADDRESS_PROOF = "ADDRESS_PROOF", "Address Proof"
        OTHER = "OTHER", "Other"

    registration_request = models.ForeignKey(
        ShopOwnerRegistrationRequest, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)

    class Meta:
        db_table = "shop_documents"
        verbose_name = "Shop Document"
        verbose_name_plural = "Shop Documents"
        indexes = [models.Index(fields=["registration_request", "document_type"])]

    def __str__(self):
        return f"{self.document_type} - {self.registration_request.shop_name}"


class ShopImage(CloudinaryAssetMixin, BaseModel):
    class ImageType(models.TextChoices):
        LOGO = "LOGO", "Shop Logo"
        BANNER = "BANNER", "Shop Banner"
        STOREFRONT = "STOREFRONT", "Storefront Photo"
        GALLERY = "GALLERY", "Gallery"

    registration_request = models.ForeignKey(
        ShopOwnerRegistrationRequest, on_delete=models.CASCADE, related_name="images"
    )
    image_type = models.CharField(max_length=20, choices=ImageType.choices, default=ImageType.GALLERY)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "shop_images"
        verbose_name = "Shop Image"
        verbose_name_plural = "Shop Images"
        indexes = [models.Index(fields=["registration_request", "image_type"])]

    def __str__(self):
        return f"{self.image_type} - {self.registration_request.shop_name}"
