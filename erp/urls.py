from django.urls import path, include
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path(
        "mentions-legales",
        views.EditorialView.as_view(
            template_name="editorial/mentions_legales.html"
        ),
        name="mentions_legales",
    ),
    path(
        "accessibilite",
        views.EditorialView.as_view(
            template_name="editorial/accessibilite.html"
        ),
        name="accessibilite",
    ),
    path(
        "contact",
        views.EditorialView.as_view(template_name="editorial/contact.html"),
        name="contact",
    ),
    path(
        "donnees-personnelles",
        views.EditorialView.as_view(
            template_name="editorial/donnees_personnelles.html"
        ),
        name="donnees_personnelles",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/",
        views.App.as_view(),
        name="commune",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/a/<int:activite>/",
        views.App.as_view(),
        name="commune_activite",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/erp/<int:erp>/",
        views.App.as_view(),
        name="commune_erp",
    ),
    path(
        # FIXME slugs
        "app/<str:commune>/a/<int:activite>/erp/<int:erp>/",
        views.App.as_view(),
        name="commune_activite_erp",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
