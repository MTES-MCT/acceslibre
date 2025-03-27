from django.urls import path
from django.views.generic import TemplateView

from compte import views

urlpatterns = [
    path("mon-profil/", views.my_profile, name="my_profile"),
    path("email/sent/", TemplateView.as_view(template_name="compte/mon_email_sent.html"), name="mon_email_sent"),
    path("email/change/<uuid:activation_token>/", views.change_email, name="change_email"),
    path("erps/", views.mes_erps, name="mes_erps"),
    path("abonnements/", views.mes_abonnements, name="mes_abonnements"),
    path("contributions/", views.mes_contributions, name="mes_contributions"),
    path("contributions/recues/", views.mes_contributions_recues, name="mes_contributions_recues"),
    path("challenges/", views.mes_challenges, name="mes_challenges"),
    path("suppression/", views.delete_account, name="delete_account"),
    path("set-api-key/", views.set_api_key, name="set_api_key"),
]
