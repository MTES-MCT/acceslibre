from django.urls import path

from auth import views

urlpatterns = [
    path("mon_compte/", views.mon_compte, name="mon_compte"),
    path("mon_compte/identifiant/", views.mon_identifiant, name="mon_identifiant"),
    path("mon_compte/email/", views.mon_email, name="mon_email"),
]
