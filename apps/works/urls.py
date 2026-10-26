from django.urls import path


from apps.works.views import (
    DeletedWorkListView,
    WorkAdvanceView,
    WorkAssignView,
    WorkDetailView,
    WorkListCreateView,
)

urlpatterns = [
    path("shops/<uuid:shop_id>/works/", WorkListCreateView.as_view(), name="work-list"),
    path(
        "shops/<uuid:shop_id>/works/deleted/",
        DeletedWorkListView.as_view(),
        name="work-deleted-list",
    ),
    path(
        "shops/<uuid:shop_id>/works/<uuid:pk>/",
        WorkDetailView.as_view(),
        name="work-detail",
    ),
    path(
        "shops/<uuid:shop_id>/works/<uuid:pk>/advance/",
        WorkAdvanceView.as_view(),
        name="work-advance",
    ),
    path(
        "shops/<uuid:shop_id>/works/<uuid:pk>/assign/",
        WorkAssignView.as_view(),
        name="work-assign",
    ),
]
