import uuid
from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.utils import timezone

from core import mattermost
from stats.queries import get_count_challenge


class Challenge(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Créateur", on_delete=models.PROTECT
    )
    nom = models.CharField(max_length=255, help_text="Nom du challenge")
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text="Identifiant d'URL (slug)",
        max_length=255,
    )
    start_date = models.DateTimeField(verbose_name="Date de début du challenge")
    end_date = models.DateTimeField(verbose_name="Date de fin du challenge (inclus)")
    nb_erp_total_added = models.BigIntegerField(default=0)
    classement = models.JSONField(default=dict)

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

    def __str__(self):
        return self.nom

    def refresh_stats(self):
        classement, self.nb_erp_total_added = get_count_challenge(
            self.start_date, self.end_date
        )
        self.classement = [
            {"username": user.username, "erp_count_published": user.erp_count_published}
            for user in classement
        ]
        self.save()


class Referer(models.Model):
    domain = models.URLField(help_text="Domaine du site réutilisateur")

    date_notification_to_mattermost = models.DateTimeField(
        null=True, verbose_name="Date de notification sur Mattermost ?"
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "Site réutilisateur"
        verbose_name_plural = "Sites réutilisateur"

    def __str__(self):
        return self.domain

    def create_notification(self):
        return self.domain

    def notif_mattermost(self):
        if self.date_notification_to_mattermost:
            return
        try:
            mattermost.send(
                "Nouveau Réutilisateur du Widget",
                attachements=[
                    {
                        "pretext": "Un nouveau domaine a été détecté :thumbsup:",
                        "text": f"- \n[Lien vers le réutilisateur]({self.domain})",
                    }
                ],
                tags=[__name__],
            )
        except Exception as e:
            raise e
        else:
            self.date_notification_to_mattermost = timezone.now()
            self.save()


class Implementation(models.Model):
    referer = models.ForeignKey(
        Referer, on_delete=models.CASCADE, related_name="implementations"
    )
    urlpath = models.URLField(help_text="Url complète")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de détection de tracking"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Date de dernier contact"
    )

    class Meta:
        ordering = ("-updated_at", "urlpath")
        verbose_name = "Implémentation du Widget"
        verbose_name_plural = "Implémentations du Widget"

    def __str__(self):
        return self.urlpath
