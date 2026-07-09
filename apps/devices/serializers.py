from rest_framework import serializers

from apps.devices.models import UserDevice


class DeviceRegistrationSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(choices=UserDevice.DeviceType.choices)
    device_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    fcm_token = serializers.CharField(max_length=500, required=False, allow_blank=True)
    app_version = serializers.CharField(max_length=20, required=False, allow_blank=True)
    os_version = serializers.CharField(max_length=20, required=False, allow_blank=True)


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = [
            "id", "device_id", "device_type", "device_name", "app_version",
            "os_version", "is_trusted", "last_active_at", "created_at",
        ]
        read_only_fields = fields
