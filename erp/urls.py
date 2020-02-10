from django.urls import path, include

from . import views

urlpatterns = [
    # FIXME: we want a proper landing page here
    path("", views.to_betagouv, name="home"),
    path("app/", views.Home.as_view(), name="app"),
    path("nested_admin/", include("nested_admin.urls")),
]
