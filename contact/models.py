from django.conf import settings
from django.db import models

from erp.models import Erp


class Message(models.Model):
    # XXX we should retrieve users with their email ?
    subject = models.CharField(verbose_name="Sujet",)
    name = models.CharField(verbose_name="Votre nom", required=False)
    email = models.EmailField(verbose_name="Adresse email",)
    body = models.CharField(verbose_name="Message",)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur", null=True, blank=False
    )
    erp = models.ForeignKey(Erp, null=True, blank=False)
    verif = models.BooleanField(verbose_name="Vérification humaine",)
    sent_ok = models.BooleanField(verbose_name="Envoi OK")
