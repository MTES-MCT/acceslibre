from django.urls import path
from django.views.generic import TemplateView

from compte import views

urlpatterns = [
    path("", views.mon_compte, name="mon_compte"),
    path("identifiant/", views.mon_identifiant, name="mon_identifiant"),
    path("email/", views.mon_email, name="mon_email"),
    path(
        "email/sent/",
        TemplateView.as_view(template_name="compte/mon_email_sent.html"),
        name="mon_email_sent",
    ),
    path(
        "email/change/<uuid:activation_token>/",
        views.change_email,
        name="change_email",
    ),
    path("erps/", views.mes_erps, name="mes_erps"),
    path("abonnements/", views.mes_abonnements, name="mes_abonnements"),
    path("contributions/", views.mes_contributions, name="mes_contributions"),
    path(
        "contributions/recues/",
        views.mes_contributions_recues,
        name="mes_contributions_recues",
    ),
    path(
        "suppression",
        views.delete_account,
        name="delete_account",
    ),
    path(
        "notifications/rappels/disable",
        views.disable_reminders,
        name="disable_reminders",
    ),
]
