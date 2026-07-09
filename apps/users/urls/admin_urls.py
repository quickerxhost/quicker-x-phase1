from django.urls import path

from apps.users.views.admin_views import (
    AdminLoginHistoryView,
    AdminUserActivateView,
    AdminUserDeactivateView,
    AdminUserDeleteView,
    AdminUserListView,
    AdminUserResetPasswordView,
)

urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<uuid:pk>/activate/", AdminUserActivateView.as_view(), name="admin-user-activate"),
    path("users/<uuid:pk>/deactivate/", AdminUserDeactivateView.as_view(), name="admin-user-deactivate"),
    path("users/<uuid:pk>/", AdminUserDeleteView.as_view(), name="admin-user-delete"),
    path("users/<uuid:pk>/reset-password/", AdminUserResetPasswordView.as_view(), name="admin-user-reset-password"),
    path("users/<uuid:pk>/login-history/", AdminLoginHistoryView.as_view(), name="admin-user-login-history"),
]
