from django.urls import path

from annuaire import views

urlpatterns = [
    path("", views.home, name="annuaire_home"),
    path(
        "<str:departement>/",
        views.departement,
        name="annuaire_departement",
    ),
]
