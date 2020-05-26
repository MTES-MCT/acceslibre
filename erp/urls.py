from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.decorators.cache import cache_page

from . import views

APP_CACHE_TTL = 60 * 5
EDITORIAL_CACHE_TTL = 60 * 60


handler403 = views.handler403
handler404 = views.handler404
handler500 = views.handler500


def app_page():
    return cache_page(APP_CACHE_TTL)(views.App.as_view())


def api_view():
    return cache_page(APP_CACHE_TTL)(views.Api.as_view())


def editorial_page(template_name):
    return cache_page(EDITORIAL_CACHE_TTL)(
        views.EditorialView.as_view(template_name=template_name)
    )


urlpatterns = [
    ############################################################################
    # Editorial
    ############################################################################
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
    ############################################################################
    # HTML app
    ############################################################################
    path("app/autocomplete/", views.autocomplete, name="autocomplete",),
    path("app/<str:commune>/", app_page(), name="commune",),
    path(
        "app/<str:commune>/a/<str:activite_slug>/", app_page(), name="commune_activite",
    ),
    path("app/<str:commune>/erp/<str:erp_slug>/", app_page(), name="commune_erp",),
    path(
        "app/<str:commune>/a/<str:activite_slug>/erp/<str:erp_slug>/",
        app_page(),
        name="commune_activite_erp",
    ),
    ############################################################################
    # Account
    ############################################################################
    path("mon_compte/", views.mon_compte, name="mon_compte"),
    path("mon_compte/erps/", views.mes_erps, name="mes_erps"),
    ############################################################################
    # Admin stuff
    ############################################################################
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="admin_password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="admin_password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="admin_password_reset_complete",
    ),
    path("nested_admin/", include("nested_admin.urls")),
]
