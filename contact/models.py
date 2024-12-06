from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as translate_lazy

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
        (TOPIC_BUG, translate_lazy("Bug technique")),
        (TOPIC_CONNECTION, translate_lazy("Problème de connexion")),
        (TOPIC_ADDRESS, translate_lazy("Adresse non reconnue")),
        (TOPIC_DELETION, translate_lazy("Suppression d'un établissement")),
        (TOPIC_CONTACT, translate_lazy("Prise de contact avec Acceslibre")),
        (TOPIC_API, translate_lazy("API")),
        (TOPIC_SIGNALEMENT, translate_lazy("Signaler une malveillance")),
        (TOPIC_API_KEY, translate_lazy("Clef API")),
        (TOPIC_AUTRE, translate_lazy("Autre")),
    ]

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["topic"]),
        ]

    topic = models.CharField(max_length=50, verbose_name=translate_lazy("Sujet"), choices=TOPICS, default=TOPIC_CONTACT)
    name = models.CharField(max_length=255, verbose_name=translate_lazy("Votre nom"), null=True, blank=True)
    email = models.EmailField(
        max_length=255,
        verbose_name=translate_lazy("Adresse email"),
        error_messages={"invalid": ""},
    )
    body = models.TextField(
        max_length=5000,
        verbose_name=translate_lazy("Message"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate_lazy("Utilisateur"),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    erp = models.ForeignKey(Erp, null=True, blank=False, on_delete=models.SET_NULL)
    sent_ok = models.BooleanField(verbose_name=translate_lazy("Envoi OK"), default=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))


class FAQ(models.Model):
    SECTION_GENERAL = "general"
    SECTION_CONTRIB = "contrib"
    SECTION_DATA = "data"
    SECTION_CHOICES = (
        (SECTION_GENERAL, translate_lazy("Utilisation générale d'acceslibre")),
        (SECTION_CONTRIB, translate_lazy("Contribution")),
        (SECTION_DATA, translate_lazy("Accès aux données")),
    )

    section = models.CharField(max_length=50, default=SECTION_GENERAL, choices=SECTION_CHOICES)
    title = models.CharField(max_length=255, verbose_name=translate_lazy("Titre"))
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))

    def __str__(self):
        return f"{self.get_section_display()} - {self.title}"
