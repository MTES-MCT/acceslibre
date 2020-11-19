from django.urls import path

from core.cache import cache_per_user
from annuaire import views

ANNUAIRE_CACHE_TTL = 60 * 60


urlpatterns = [
    path("", cache_per_user(ANNUAIRE_CACHE_TTL)(views.home), name="annuaire_home"),
    path(
        "<str:departement>/",
        cache_per_user(ANNUAIRE_CACHE_TTL)(views.departement),
        name="annuaire_departement",
    ),
]
