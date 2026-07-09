from rest_framework.routers import DefaultRouter

from apps.roles.views import PermissionViewSet, RoleViewSet

router = DefaultRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"", RoleViewSet, basename="role")

urlpatterns = router.urls
