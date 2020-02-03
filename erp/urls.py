from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(r"nested_admin/", include("nested_admin.urls")),
]
