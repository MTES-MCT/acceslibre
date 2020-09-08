from django.conf import settings
from django.db import models

from erp.models import Erp


class Message(models.Model):
    TOPICS = [
        ("bug", "Rapport de bug"),
        ("support", "Demande d'aide"),
        ("contact", "Prise de contact"),
        ("partenariat", "Proposition de partenariat"),
        ("signalement", "Signalement d'un problème de données"),
        ("autre", "Autre demande"),
    ]

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["topic"]),
        ]

    topic = models.CharField(max_length=50, verbose_name="Sujet", choices=TOPICS)
    name = models.CharField(
        max_length=255, verbose_name="Votre nom", null=True, blank=True
    )
    email = models.EmailField(max_length=255, verbose_name="Adresse email",)
    body = models.TextField(max_length=5000, verbose_name="Message",)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Utilisateur",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
    )
    erp = models.ForeignKey(Erp, null=True, blank=False, on_delete=models.SET_NULL)
    sent_ok = models.BooleanField(verbose_name="Envoi OK")

    # Datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )
