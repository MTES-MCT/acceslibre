from django.urls import include, path
from rest_framework import routers
from .views import AccessibiliteViewSet, ActiviteViewSet, ErpViewSet

router = routers.DefaultRouter()
router.register(r"accessibilite", AccessibiliteViewSet)
router.register(r"activites", ActiviteViewSet)
router.register(r"erps", ErpViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "api-auth/", include("rest_framework.urls", namespace="rest_framework")
    ),
]
