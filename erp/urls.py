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
    path("app/<str:commune>/", views.App.as_view(), name="commune",),
    path(
        "app/<str:commune>/a/<str:activite_slug>/",
        views.App.as_view(),
        name="commune_activite",
    ),
    path(
        "app/<str:commune>/erp/<str:erp_slug>/",
        views.App.as_view(),
        name="commune_erp",
    ),
    path(
        "app/<str:commune>/a/<str:activite_slug>/erp/<str:erp_slug>/",
        views.App.as_view(),
        name="commune_activite_erp",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
