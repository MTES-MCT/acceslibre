from django.urls import path, include

from . import views

urlpatterns = [
    # FIXME: we want a proper landing page here
    path("", views.to_betagouv, name="home"),
    path("app/", views.home, name="app"),
    path(
        # FIXME slugs
        "app/commune/<str:commune>/",
        views.Commune.as_view(),
        name="commune",
    ),
    path(
        # FIXME slugs
        "app/commune/<str:commune>/<str:activite>/",
        views.Commune.as_view(),
        name="commune_activite",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
