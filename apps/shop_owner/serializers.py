from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.validators import validate_phone_number
from apps.shop_owner.models import ShopDocument, ShopImage, ShopOwnerRegistrationRequest
from apps.shop_owner.services.cloudinary_service import upload_to_cloudinary


class ShopDocumentOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopDocument
        fields = [
            "id", "document_type", "public_id", "secure_url", "resource_type",
            "width", "height", "bytes", "format", "created_at",
        ]
        read_only_fields = fields


class ShopImageOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopImage
        fields = [
            "id", "image_type", "display_order", "public_id", "secure_url",
            "resource_type", "width", "height", "bytes", "format", "created_at",
        ]
        read_only_fields = fields


class ShopOwnerRegistrationRequestSerializer(serializers.ModelSerializer):
    """
    Input serializer for POST /api/v1/shop-owner/register-request/.

    Accepts the full registration form as multipart/form-data:
    text fields + document_<type> file fields + image_<type> file fields.
    Field names must be reconciled exactly against the Flutter Shop Owner UI form.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    owner_phone_number = serializers.CharField(validators=[validate_phone_number])

    # Documents (each optional at the serializer level; business rules on
    # which are mandatory can be enforced in validate() once the UI spec is final).
    document_gst_certificate = serializers.FileField(required=False, write_only=True)
    document_pan_card = serializers.FileField(required=False, write_only=True)
    document_fssai_license = serializers.FileField(required=False, write_only=True)
    document_shop_license = serializers.FileField(required=False, write_only=True)
    document_identity_proof = serializers.FileField(required=False, write_only=True)
    document_address_proof = serializers.FileField(required=False, write_only=True)

    image_logo = serializers.FileField(required=False, write_only=True)
    image_banner = serializers.FileField(required=False, write_only=True)
    image_storefront = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = ShopOwnerRegistrationRequest
        fields = [
            "owner_full_name", "owner_email", "owner_phone_number", "owner_date_of_birth",
            "password",
            "shop_name", "business_type", "shop_category", "shop_description",
            "gstin", "pan_number", "fssai_license_number",
            "address_line1", "address_line2", "city", "state", "postal_code", "country",
            "latitude", "longitude",
            "bank_account_holder_name", "bank_account_number", "bank_ifsc_code", "bank_name",
            "document_gst_certificate", "document_pan_card", "document_fssai_license",
            "document_shop_license", "document_identity_proof", "document_address_proof",
            "image_logo", "image_banner", "image_storefront",
        ]

    def _extract_files(self, validated_data):
        document_map = {
            "document_gst_certificate": ShopDocument.DocumentType.GST_CERTIFICATE,
            "document_pan_card": ShopDocument.DocumentType.PAN_CARD,
            "document_fssai_license": ShopDocument.DocumentType.FSSAI_LICENSE,
            "document_shop_license": ShopDocument.DocumentType.SHOP_LICENSE,
            "document_identity_proof": ShopDocument.DocumentType.IDENTITY_PROOF,
            "document_address_proof": ShopDocument.DocumentType.ADDRESS_PROOF,
        }
        image_map = {
            "image_logo": ShopImage.ImageType.LOGO,
            "image_banner": ShopImage.ImageType.BANNER,
            "image_storefront": ShopImage.ImageType.STOREFRONT,
        }

        documents = []
        for field, doc_type in document_map.items():
            file_obj = validated_data.pop(field, None)
            if file_obj:
                meta = upload_to_cloudinary(file_obj, folder=f"quicker-x/shop-documents/{doc_type.lower()}")
                documents.append(ShopDocument(document_type=doc_type, **meta))

        images = []
        for field, img_type in image_map.items():
            file_obj = validated_data.pop(field, None)
            if file_obj:
                meta = upload_to_cloudinary(file_obj, folder=f"quicker-x/shop-images/{img_type.lower()}")
                images.append(ShopImage(image_type=img_type, **meta))

        return documents, images

    def create(self, validated_data):
        from apps.shop_owner.services.registration_service import create_shop_owner_registration

        documents, images = self._extract_files(validated_data)
        return create_shop_owner_registration(
            validated_data=validated_data, documents=documents, images=images
        )


class ShopOwnerRegistrationRequestOutputSerializer(serializers.ModelSerializer):
    documents = ShopDocumentOutputSerializer(many=True, read_only=True)
    images = ShopImageOutputSerializer(many=True, read_only=True)

    class Meta:
        model = ShopOwnerRegistrationRequest
        fields = [
            "id", "shop_name", "owner_full_name", "owner_email", "owner_phone_number",
            "business_type", "shop_category", "status", "city", "state",
            "reviewed_at", "rejection_reason", "documents", "images", "created_at",
        ]
        read_only_fields = fields


class ShopOwnerRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500)


class ShopOwnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
