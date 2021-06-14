from django.urls import path

from compte import views

urlpatterns = [
    path("", views.mon_compte, name="mon_compte"),
    path("identifiant/", views.mon_identifiant, name="mon_identifiant"),
    path("email/", views.mon_email, name="mon_email"),
    path(
        "email/change/<uuid:activation_token>/",
        views.change_email,
        name="change_email",
    ),
]
