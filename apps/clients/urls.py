from django.urls import path

from apps.clients.views import (
    ClientDetailView,
    ClientListCreateView,
    RelatedPersonDetailView,
    RelatedPersonListCreateView,
)

urlpatterns = [
    path(
        "shops/<uuid:shop_id>/clients/",
        ClientListCreateView.as_view(),
        name="client-list",
    ),
    path(
        "shops/<uuid:shop_id>/clients/<uuid:pk>/",
        ClientDetailView.as_view(),
        name="client-detail",
    ),
    path(
        "shops/<uuid:shop_id>/clients/<uuid:client_id>/related-persons/",
        RelatedPersonListCreateView.as_view(),
        name="related-person-list",
    ),
    path(
        "shops/<uuid:shop_id>/clients/<uuid:client_id>/related-persons/<uuid:pk>/",
        RelatedPersonDetailView.as_view(),
        name="related-person-detail",
    ),
]
