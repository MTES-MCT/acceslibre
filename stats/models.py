import uuid

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as translate

from stats.queries import get_count_challenge, get_erp_counts_histogram, get_stats_territoires, get_top_contributors


class GlobalStats(models.Model):
    _singleton = models.BooleanField(default=True, editable=False, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    erp_counts_histogram = models.JSONField(default=dict)
    stats_territoires_sort_count = models.JSONField(default=dict)
    stats_territoires_sort_default = models.JSONField(default=dict)
    top_contributors = models.JSONField(default=dict)

    class Meta:
        verbose_name = translate("Statistiques")
        verbose_name_plural = translate("Statistiques")

    @classmethod
    def refresh_stats(cls):
        self, created = cls.objects.get_or_create()
        self.erp_counts_histogram = get_erp_counts_histogram()
        self.stats_territoires_sort_count = get_stats_territoires(sort="count")
        self.stats_territoires_sort_default = get_stats_territoires()
        self.top_contributors = list(get_top_contributors())
        self.save()

    def get_stats_territoires(self, sort):
        if sort == "count":
            return self.stats_territoires_sort_count
        else:
            return self.stats_territoires_sort_default


class Challenge(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=translate("Créateur"), on_delete=models.PROTECT
    )
    nom = models.CharField(max_length=255, help_text=translate("Nom du challenge"))
    accroche = models.TextField(null=True, blank=True)
    text_reserve = models.TextField(null=True, blank=True)
    objectif = models.TextField(null=True, blank=True)
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text=translate("Identifiant d'URL (slug)"),
        max_length=255,
    )
    start_date = models.DateTimeField(verbose_name=translate("Date de début du challenge"))
    end_date = models.DateTimeField(verbose_name=translate("Date de fin du challenge (inclus)"))
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="stats.ChallengePlayer",
        related_name="challenge_players",
    )
    nb_erp_total_added = models.BigIntegerField(default=0)
    classement = models.JSONField(default=dict)

    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("nom",)
        verbose_name = translate("Challenge")
        verbose_name_plural = translate("Challenges")

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("challenge-detail", kwargs={"challenge_slug": self.slug})

    @property
    def has_open_inscription(self):
        return timezone.now() < self.end_date and timezone.now() >= self.start_date

    def refresh_stats(self):
        if self.nom == "Challenge DDT":
            return  # do not update this challenge

        if self.nom == "Challenge de l’été beta.gouv":
            emails_players_list = (
                get_user_model().objects.filter(email__contains="@beta.gouv.fr").values_list("email", flat=True)
            )
        elif self.pk == 3:  # Challenge Semaine du handicap à Antony
            emails_players_list = (
                get_user_model().objects.filter(email__contains="@ville-antony.fr").values_list("email", flat=True)
            )
        else:
            emails_players_list = self.players.all().values_list("email", flat=True)

        classement, self.nb_erp_total_added = get_count_challenge(self.start_date, self.end_date, emails_players_list)
        self.classement = [
            {"username": user.username, "erp_count_published": user.erp_count_published} for user in classement
        ]
        self.save()


class ChallengePlayer(models.Model):
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate("Joueur"),
        on_delete=models.PROTECT,
        related_name="inscriptions",
    )
    challenge = models.ForeignKey(
        "stats.Challenge",
        verbose_name=translate("Challenge"),
        on_delete=models.PROTECT,
        related_name="inscriptions",
    )
    inscription_date = models.DateTimeField(verbose_name=translate("Date d'inscription"), auto_now_add=True)

    class Meta:
        ordering = ("inscription_date",)
        verbose_name = translate("Challenge Player")
        verbose_name_plural = translate("Challenges Players")

    def __str__(self):
        return f"{self.player} - {self.challenge}"


class Referer(models.Model):
    domain = models.URLField(help_text=translate("Domaine du site réutilisateur"), unique=True)

    date_notification_to_mattermost = models.DateTimeField(
        null=True, verbose_name=translate("Date de notification sur Mattermost ?")
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = translate("Site réutilisateur")
        verbose_name_plural = translate("Sites réutilisateur")
        indexes = [
            models.Index(fields=["domain"], name="domain_idx"),
        ]

    def __str__(self):
        return self.domain


class Implementation(models.Model):
    referer = models.ForeignKey(Referer, on_delete=models.CASCADE, related_name="implementations")
    urlpath = models.URLField(help_text=translate("Url complète"), unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate("Date de détection de tracking"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate("Date de dernier contact"))

    class Meta:
        ordering = ("-updated_at", "urlpath")
        verbose_name = translate("Implémentation du Widget")
        verbose_name_plural = translate("Implémentations du Widget")
        indexes = [
            models.Index(fields=["referer"], name="referer_idx"),
            models.Index(fields=["urlpath"], name="urlpath_idx"),
        ]

    def __str__(self):
        return self.urlpath


class WidgetEvent(models.Model):
    date = models.DateField(auto_now_add=True)
    domain = models.URLField(help_text=translate("Domaine du site réutilisateur"))
    referer_url = models.URLField(help_text=translate("Url complète"))
    views = models.IntegerField(default=0)

    class Meta:
        unique_together = ("domain", "referer_url", "date")
