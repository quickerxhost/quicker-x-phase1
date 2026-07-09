from rest_framework import serializers

from apps.addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "address_type", "label", "line1", "line2", "landmark",
            "city", "state", "country", "postal_code", "latitude", "longitude",
            "is_default", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        validated_data["created_by"] = request.user
        if validated_data.get("is_default"):
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        return super().create(validated_data)
