from django.urls import path

from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.devices.serializers import DeviceRegistrationSerializer, UserDeviceSerializer
from apps.users.views.profile_views import MeView
from rest_framework import generics, permissions, views
from apps.core.responses import success_response


class MyAddressListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/me/addresses/
    POST /api/v1/users/me/addresses/
    """

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success_response(data=response.data, message="Addresses retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Address added successfully.", status_code=201)


class MyAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/v1/users/me/addresses/{id}/
    """

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete(actor=request.user)
        return success_response(message="Address removed successfully.")


class RegisterDeviceView(views.APIView):
    """POST /api/v1/users/me/devices/ — register/update a device for push + session tracking."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from apps.users.services.auth_service import register_device

        serializer = DeviceRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        device = register_device(
            request.user, data["device_id"], data["device_type"], data.get("fcm_token")
        )
        return success_response(
            data=UserDeviceSerializer(device).data, message="Device registered successfully."
        )


urlpatterns = [
    path("me/", MeView.as_view(), name="users-me"),
    path("me/addresses/", MyAddressListCreateView.as_view(), name="users-me-addresses"),
    path("me/addresses/<uuid:id>/", MyAddressDetailView.as_view(), name="users-me-address-detail"),
    path("me/devices/", RegisterDeviceView.as_view(), name="users-me-devices"),
]
