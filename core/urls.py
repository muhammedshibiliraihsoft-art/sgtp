"""
URL configuration for Django project.
"""

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.api_documentation import internal_api_documentation
from core.health import health_live, health_ready

api_v1_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.tenants.urls")),
    path("", include("apps.clients.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url=reverse_lazy("swagger-ui"), permanent=False)),
    # Versioned API routes
    path("api/v1/", include((api_v1_patterns, "v1"))),
    # Health Probes
    path("api/health/live/", health_live, name="health_live"),
    path("api/health/ready/", health_ready, name="health_ready"),
    # API Documentation
    path(
        "api/schema/",
        internal_api_documentation(
            SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[])
        ),
        name="schema",
    ),
    path(
        "api/docs/",
        internal_api_documentation(SpectacularSwaggerView.as_view(url_name="schema")),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
