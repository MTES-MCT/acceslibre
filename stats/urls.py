from django.urls import path

from core.cache import cache_per_user_function
from . import views

STATS_CACHE_TTL = 60 * 5

urlpatterns = [
    path(
        "",
        cache_per_user_function(STATS_CACHE_TTL)(views.StatsView.as_view()),
        name="stats_home",
    ),
]
