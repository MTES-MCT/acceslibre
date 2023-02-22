from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", views.contact, name="contact_form"),
    path("<str:topic>/", views.contact, name="contact_topic"),
    path("<str:topic>/<str:erp_slug>/", views.contact, name="contact_topic_erp"),
    path(
        "sent",
        TemplateView.as_view(template_name="contact_form/contact_form_sent.html"),
        name="contact_form_sent",
    ),
]
