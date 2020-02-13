from django.urls import path, include

from . import views

urlpatterns = [
    # path("", views.to_betagouv, name="home"),
    path("", views.home, name="app"),
    path(
        # FIXME slugs
        "app/<str:commune>/",
        views.App.as_view(),
        name="commune",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/<int:activite>/",
        views.App.as_view(),
        name="commune_activite",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/<int:activite>/<int:erp>/",
        views.App.as_view(),
        name="commune_activite_erp",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
