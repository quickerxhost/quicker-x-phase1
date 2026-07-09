from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Bare root ("/") had no route at all, so it 404'd both locally and on
    # Render. This just redirects it to the API docs instead of a dead page.
    path("", RedirectView.as_view(url="/api/docs/", permanent=False)),

    path("django-admin/", admin.site.urls),

    # OpenAPI schema + docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Versioned API
    path("api/v1/", include("config.api_v1_urls")),

    # NOTE: Backward-compatible aliases (no version prefix).
    # Added only so older client builds calling e.g. /auth/register/ instead
    # of /api/v1/auth/register/ keep working. Does not change or remove any
    # existing route above — /api/v1/... remains the primary, documented API.
    path("", include("config.api_v1_urls")),
]
