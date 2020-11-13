from django.conf import settings
from django.db import models

from erp.models import Erp


class Message(models.Model):
    TOPIC_A11Y = "a11y"
    TOPIC_BUG = "bug"
    TOPIC_SUPPORT = "support"
    TOPIC_CONTACT = "contact"
    TOPIC_PARTENARIAT = "partenariat"
    TOPIC_SIGNALEMENT = "signalement"
    TOPIC_AUTRE = "autre"
    TOPICS = [
        (TOPIC_A11Y, "Problème d'accessibilité"),
        (TOPIC_BUG, "Rapport de bug"),
        (TOPIC_SUPPORT, "Demande d'aide"),
        (TOPIC_CONTACT, "Prise de contact"),
        (TOPIC_PARTENARIAT, "Proposition de partenariat"),
        (TOPIC_SIGNALEMENT, "Signalement d'un problème de données"),
        (TOPIC_AUTRE, "Autre demande"),
    ]

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["topic"]),
        ]

    topic = models.CharField(
        max_length=50, verbose_name="Sujet", choices=TOPICS, default=TOPIC_CONTACT
    )
    name = models.CharField(
        max_length=255, verbose_name="Votre nom", null=True, blank=True
    )
    email = models.EmailField(
        max_length=255,
        verbose_name="Adresse email",
    )
    body = models.TextField(
        max_length=5000,
        verbose_name="Message",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    erp = models.ForeignKey(Erp, null=True, blank=False, on_delete=models.SET_NULL)
    sent_ok = models.BooleanField(verbose_name="Envoi OK", default=False)

    # Datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )
