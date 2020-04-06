from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers
from .views import AccessibiliteViewSet, ActiviteViewSet, ErpViewSet

router = routers.DefaultRouter()
router.register(r"accessibilite", AccessibiliteViewSet)
router.register(r"activites", ActiviteViewSet)
router.register(r"erps", ErpViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "swagger-ui/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
    path(
        "api-auth/", include("rest_framework.urls", namespace="rest_framework")
    ),
]
