from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.users.urls.auth_urls")),
    path("users/", include("apps.users.urls.user_urls")),
    path("shop-owner/", include("apps.shop_owner.urls.shop_owner_urls")),
    path("admin/", include("apps.users.urls.admin_urls")),
    path("admin/shop-owner/", include("apps.shop_owner.urls.admin_urls")),
    path("roles/", include("apps.roles.urls")),
]
