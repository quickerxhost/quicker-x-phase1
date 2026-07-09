from rest_framework import serializers

from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.profiles.models import UserProfile
from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "avatar_public_id", "avatar_secure_url", "date_of_birth", "gender",
            "bio", "preferred_language", "marketing_opt_in",
        ]


class MeSerializer(serializers.ModelSerializer):
    """
    Full 'current user' representation returned by
    GET /api/v1/users/me/ and PATCH /api/v1/users/me/.
    """

    profile = UserProfileSerializer()
    addresses = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "phone_number", "full_name", "account_type",
            "is_email_verified", "is_phone_verified", "profile", "addresses",
            "roles", "created_at",
        ]
        read_only_fields = ["id", "phone_number", "account_type", "created_at", "roles"]

    def get_addresses(self, obj):
        addresses = Address.objects.filter(user=obj)
        return AddressSerializer(addresses, many=True).data

    def get_roles(self, obj):
        return list(obj.active_roles)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.updated_by = instance
            profile.save()

        return instance
