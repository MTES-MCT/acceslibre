from django.urls import path

from . import views

urlpatterns = [
    path(
        "",
        views.stats,
        name="stats_home",
    ),
    path(
        "territoires/",
        views.territoires,
        name="stats_territoires",
    ),
]
