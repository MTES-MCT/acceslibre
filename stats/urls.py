from django.urls import path

from core.cache import cache_per_user
from . import views

STATS_CACHE_TTL = 60 * 5


urlpatterns = [
    path(
        "",
        cache_per_user(STATS_CACHE_TTL)(views.stats),
        name="stats_home",
    ),
    path(
        "territoires/",
        cache_per_user(STATS_CACHE_TTL)(views.territoires),
        name="stats_territoires",
    ),
]
