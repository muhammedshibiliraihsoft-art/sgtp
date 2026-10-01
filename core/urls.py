"""
URL configuration for Django project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.tenants.urls')),
    path('', include('apps.clients.urls')),
]

from core.health import health_live, health_ready

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='api_test.html'), name='api_test'),
    path('api-auth/', include('rest_framework.urls')),

    # Versioned API routes
    path('api/v1/', include((api_v1_patterns, 'v1'))),

    # Health Probes
    path('api/health/live/', health_live, name='health_live'),
    path('api/health/ready/', health_ready, name='health_ready'),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
