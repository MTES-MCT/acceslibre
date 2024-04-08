import uuid

from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as translate

from stats.queries import get_challenge_scores, get_erp_counts_histogram, get_top_contributors


class GlobalStats(models.Model):
    _singleton = models.BooleanField(default=True, editable=False, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    erp_counts_histogram = models.JSONField(default=dict)
    top_contributors = models.JSONField(default=dict)

    class Meta:
        verbose_name = translate("Statistiques")
        verbose_name_plural = translate("Statistiques")

    @classmethod
    def refresh_stats(cls):
        self, _ = cls.objects.get_or_create()
        self.erp_counts_histogram = get_erp_counts_histogram()
        self.top_contributors = list(get_top_contributors())
        self.save()


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
    classement_team = models.JSONField(default=dict)

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

    @property
    def version(self):
        # NOTE: naive versionning, v1 challenges are intended to be deprecated soon, just here to manage a distinct display
        return "v2" if self.end_date.year >= 2024 else "v1"

    def refresh_stats(self):
        players = {user.pk: user.username for user in self.players.all()}
        teams = {
            team_pk: team_name for team_pk, team_name in self.inscriptions.all().values_list("team__pk", "team__name")
        }

        scores_per_user_id, scores_per_team_id = get_challenge_scores(
            self, self.start_date, self.end_date, players.keys()
        )
        self.classement = [
            {"username": players.get(user_id), "nb_access_info_changed": max(score, 0)}
            for user_id, score in scores_per_user_id
        ]
        self.classement_team = (
            [
                {"team": teams.get(team_id), "nb_access_info_changed": max(score, 0)}
                for team_id, score in scores_per_team_id
            ]
            if scores_per_team_id
            else None
        )
        self.nb_erp_total_added = sum([score for _, score in scores_per_user_id])
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
    team = models.ForeignKey(
        "stats.ChallengeTeam",
        verbose_name=translate("Challenge Team"),
        on_delete=models.PROTECT,
        related_name="players",
        blank=True,
        null=True,
    )
    inscription_date = models.DateTimeField(verbose_name=translate("Date d'inscription"), auto_now_add=True)

    class Meta:
        ordering = ("inscription_date",)
        verbose_name = translate("Challenge Player")
        verbose_name_plural = translate("Challenges Players")

    def __str__(self):
        str_repr = f"{self.player} - {self.challenge}"
        if self.team:
            str_repr = f"{str_repr} (team {self.team})"
        return str_repr


class ChallengeTeam(models.Model):
    name = models.CharField(max_length=255, help_text=translate("Nom de l'équipe"))

    def __str__(self):
        return f"Team {self.name}"


class WidgetEvent(models.Model):
    date = models.DateField(auto_now_add=True)
    domain = models.URLField(help_text=translate("Domaine du site réutilisateur"))
    referer_url = models.URLField(help_text=translate("Url complète"))
    views = models.IntegerField(default=0)

    class Meta:
        unique_together = ("domain", "referer_url", "date")
