from django.urls import path, include
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from . import views

APP_CACHE_TTL = 60 * 5
EDITORIAL_CACHE_TTL = 60 * 60


def app_page():
    return cache_page(APP_CACHE_TTL)(views.App.as_view())


def editorial_page(template_name):
    return cache_page(EDITORIAL_CACHE_TTL)(
        views.EditorialView.as_view(template_name=template_name)
    )


urlpatterns = [
    path("", views.home, name="home"),
    path(
        "mentions-legales",
        editorial_page("editorial/mentions_legales.html"),
        name="mentions_legales",
    ),
    path(
        "accessibilite",
        editorial_page("editorial/accessibilite.html"),
        name="accessibilite",
    ),
    path("contact", editorial_page("editorial/contact.html"), name="contact",),
    path(
        "donnees-personnelles",
        editorial_page("editorial/donnees_personnelles.html"),
        name="donnees_personnelles",
    ),
    path("app/<str:commune>/", app_page(), name="commune",),
    path(
        "app/<str:commune>/autocomplete/",
        views.autocomplete,
        name="commune_autocomplete",
    ),
    path(
        "app/<str:commune>/a/<str:activite_slug>/",
        app_page(),
        name="commune_activite",
    ),
    path(
        "app/<str:commune>/erp/<str:erp_slug>/", app_page(), name="commune_erp",
    ),
    path(
        "app/<str:commune>/a/<str:activite_slug>/erp/<str:erp_slug>/",
        app_page(),
        name="commune_activite_erp",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
