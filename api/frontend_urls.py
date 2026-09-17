from django.urls import path

from api import frontend_views

urlpatterns = [
    # NOTE: this module is included *before* erp.urls in the root URLconf, otherwise
    # `recherche/<str:commune_slug>/` would shadow `recherche/erps/`.
    path("recherche/erps/", frontend_views.FrontendErpListView.as_view(), name="front_erp_list"),
    path(
        "traduire/accessibilite/<int:pk>/",
        frontend_views.translate_accessibilite_field,
        name="front_accessibilite_translate",
    ),
]
