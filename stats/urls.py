from django.urls import path, include
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    path("", views.StatsView.as_view(), name="stats_home"),
]
