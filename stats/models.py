import uuid
from collections import defaultdict
from datetime import timedelta

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as translate

from stats.queries import get_challenge_scores


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

    users_can_register = models.BooleanField(
        default=True,
        verbose_name=translate("Les utilisateur s'auto inscrivent"),
        help_text=translate("Les utilisateurs peuvent-ils s'inscrire d'eux mêmes au challenge?"),
    )
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
    def has_open_subscriptions(self):
        return self.users_can_register and self.is_in_progress

    @property
    def is_in_progress(self):
        return not self.is_finished and timezone.now() >= self.start_date

    @property
    def is_finished(self):
        return timezone.now() > self.end_date

    @property
    def version(self):
        # NOTE: naive versionning, v1 challenges are intended to be deprecated soon, just here to manage a distinct display
        return "v2" if self.end_date.year >= 2024 else "v1"

    def _get_users_indexed_user_by_id(self, user_ids):
        users = User.objects.filter(pk__in=user_ids).values("id", "username")
        users_by_id = {user["id"]: user["username"] for user in users}
        return users_by_id

    def get_classement(self):
        if self.version == "v1":
            user_ids = [entry["user_id"] for entry in self.classement]
            users_by_id = self._get_users_indexed_user_by_id(user_ids)
            classement = [
                {"username": users_by_id.get(k["user_id"]), "erp_count_published": k["erp_count_published"]}
                for k in self.classement
            ]
            return classement

        classement = defaultdict(int)
        for scores in self.classement.values():
            for score in scores:
                classement[score["user_id"]] += score["nb_access_info_changed"]

        users_by_id = self._get_users_indexed_user_by_id(user_ids=classement.keys())
        classement = [{"username": users_by_id.get(k), "nb_access_info_changed": v} for k, v in classement.items()]
        return sorted(classement, key=lambda elt: elt["nb_access_info_changed"], reverse=True)

    def get_classement_team(self):
        if self.version == "v1":
            return self.classement_team

        classement = defaultdict(int)
        for scores in self.classement_team.values():
            for score in scores:
                classement[score["team"]] += score["nb_access_info_changed"]

        classement = [{"team": k, "nb_access_info_changed": v} for k, v in classement.items()]
        return sorted(classement, key=lambda elt: elt["nb_access_info_changed"], reverse=True)

    def refresh_stats(self):
        player_ids = list(self.players.values_list("id", flat=True))
        teams = {
            team_pk: team_name for team_pk, team_name in self.inscriptions.all().values_list("team__pk", "team__name")
        }

        for nb_days_diff in range(1, (self.end_date - self.start_date).days + 2):
            from_date = (self.start_date + timedelta(days=nb_days_diff)).replace(hour=0, minute=0, second=0)
            to_date = from_date + timedelta(days=1)

            if f"{from_date}" in self.classement:
                continue

            if to_date > timezone.now():
                continue

            scores_per_user_id, scores_per_team_id = get_challenge_scores(self, from_date, to_date, player_ids)

            self.classement[f"{from_date}"] = [
                {"user_id": user_id, "nb_access_info_changed": max(score, 0)}
                for user_id, score in scores_per_user_id.items()
            ]

            self.classement_team[f"{from_date}"] = (
                [
                    {"team": teams.get(team_id), "nb_access_info_changed": max(score, 0)}
                    for team_id, score in scores_per_team_id.items()
                ]
                if scores_per_team_id
                else []
            )

        self.nb_erp_total_added = 0
        for day in self.classement:
            self.nb_erp_total_added += sum([score["nb_access_info_changed"] for score in self.classement[day]])
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
