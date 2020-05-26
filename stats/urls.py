from django.urls import path

from . import views


urlpatterns = [
    path("", views.StatsView.as_view(), name="stats_home"),
]
