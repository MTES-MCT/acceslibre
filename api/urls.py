from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view

from .views import API_DOC_SUMMARY, AccessibiliteViewSet, ActiviteViewSet, ErpViewSet

router = routers.DefaultRouter()
router.register(r"accessibilite", AccessibiliteViewSet)
router.register(r"activites", ActiviteViewSet)
router.register(r"erps", ErpViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "openapi",
        get_schema_view(
            title="Documentation de l'API",
            description=API_DOC_SUMMARY,
            version="1.0.0",
            url="/api/",
            urlconf="api.urls",
            permission_classes=[AllowAny],
            public=True,
        ),
        name="openapi-schema",
    ),
    path(
        "docs/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="apidocs",
    ),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
