from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantMemberViewSet

router = DefaultRouter()
router.register(r'tenants', TenantViewSet)
router.register(r'memberships', TenantMemberViewSet)

urlpatterns = [
    path('', include(router.urls)),
]