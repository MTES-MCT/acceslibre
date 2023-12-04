from django.conf import settings
from django.db import models
from django.utils.translation import gettext as translate

from erp.models import Erp


class Message(models.Model):
    TOPIC_BUG = "bug"
    TOPIC_CONNECTION = "connection"
    TOPIC_ADDRESS = "address"
    TOPIC_DELETION = "deletion"
    TOPIC_CONTACT = "contact"
    TOPIC_SIGNALEMENT = "signalement"
    TOPIC_API = "api"
    TOPIC_API_KEY = "api_key"
    TOPIC_AUTRE = "autre"
    TOPICS = [
        (TOPIC_BUG, translate("Bug technique")),
        (TOPIC_CONNECTION, translate("Problème de connexion")),
        (TOPIC_ADDRESS, translate("Adresse non reconnue")),
        (TOPIC_DELETION, translate("Suppression d'un établissement")),
        (TOPIC_CONTACT, translate("Prise de contact avec Acceslibre")),
        (TOPIC_API, translate("API")),
        (TOPIC_SIGNALEMENT, translate("Signaler une malveillance")),
        (TOPIC_API_KEY, translate("Clef API")),
        (TOPIC_AUTRE, translate("Autre")),
    ]

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["topic"]),
        ]

    topic = models.CharField(max_length=50, verbose_name=translate("Sujet"), choices=TOPICS, default=TOPIC_CONTACT)
    name = models.CharField(max_length=255, verbose_name=translate("Votre nom"), null=True, blank=True)
    email = models.EmailField(
        max_length=255,
        verbose_name=translate("Adresse email"),
        error_messages={"invalid": ""},
    )
    body = models.TextField(
        max_length=5000,
        verbose_name=translate("Message"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate("Utilisateur"),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    erp = models.ForeignKey(Erp, null=True, blank=False, on_delete=models.SET_NULL)
    sent_ok = models.BooleanField(verbose_name=translate("Envoi OK"), default=False)

    # Datetimes
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate("Dernière modification"))
