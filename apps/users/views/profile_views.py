from rest_framework import permissions, views

from apps.core.responses import success_response
from apps.profiles.serializers import MeSerializer


class MeView(views.APIView):
    """
    GET   /api/v1/users/me/
    PATCH /api/v1/users/me/
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return success_response(data=serializer.data, message="Profile retrieved successfully.")

    def patch(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated successfully.")
