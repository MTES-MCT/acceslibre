from django.urls import path

from api import frontend_views

urlpatterns = [
    path("search/erps/", frontend_views.FrontendErpListView.as_view(), name="front_erp_list"),
    path(
        "translate/accessibility/<int:pk>/",
        frontend_views.translate_accessibility_field,
        name="front_accessibility_translate",
    ),
]
