import uuid

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core import mattermost
from stats.queries import get_count_challenge, get_erp_counts_histogram, get_stats_territoires, get_top_contributors


class GlobalStats(models.Model):
    _singleton = models.BooleanField(default=True, editable=False, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    erp_counts_histogram = models.JSONField(default=dict)
    stats_territoires_sort_count = models.JSONField(default=dict)
    stats_territoires_sort_default = models.JSONField(default=dict)
    top_contributors = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Statistiques"
        verbose_name_plural = "Statistiques"

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

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Créateur", on_delete=models.PROTECT)
    nom = models.CharField(max_length=255, help_text="Nom du challenge")
    accroche = models.TextField(null=True, blank=True)
    text_reserve = models.TextField(null=True, blank=True)
    objectif = models.TextField(null=True, blank=True)
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text="Identifiant d'URL (slug)",
        max_length=255,
    )
    start_date = models.DateTimeField(verbose_name="Date de début du challenge")
    end_date = models.DateTimeField(verbose_name="Date de fin du challenge (inclus)")
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
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("challenge-detail", kwargs={"challenge_slug": self.slug})

    @property
    def has_open_inscription(self):
        return timezone.now() < self.end_date and timezone.now() >= self.start_date

    def refresh_stats(self):
        if self.nom == "Challenge DDT":
            emails_players_list = [
                "gauthierlaprade@gmail.com",
                "magali.vainjac@savoie.gouv.fr",
                "roxane.herin@savoie.gouv.fr",
                "christel.condemine@savoie.gouv.fr",
                "jean-christophe.henrotte@savoie.gouv.fr",
                "sophie.lucas@aube.gouv.fr",
                "frederic.chaal@aube.gouv.fr",
                "thomas.lapierre@aube.gouv.fr",
                "sabine.lemoine@aube.gouv.fr",
                "stephane.mulat@aube.gouv.fr",
                "carine.rudelle@aveyron.gouv.fr",
                "veronique.bex@aveyron.gouv.fr",
                "nadine.negre@aveyron.gouv.fr",
                "bernadette.denoit@aveyron.gouv.fr",
                "emmanuelle.esteve-chellali@aveyron.gouv.fr",
                "ddt-sh@haute-savoie.gouv.fr",
                "lea.pelissier@haute-savoie.gouv.fr",
                "martine.excoffier@haute-savoie.gouv.fr",
                "josiane.tomasin@haute-savoie.gouv.fr",
                "jerome.ramanzin@haute-savoie.gouv.fr",
                "sophie.tcheng@developpement-durable.gouv.fr",
                "gauthier.laprade@i-carre.net",
                "laurence.monnet@developpement-durable.gouv.fr",
                "delphine.millot@meuse.gouv.fr",
                "ddt-scdt-ats@meuse.gouv.fr",
                "christelle.defloraine@meuse.gouv.fr",
                "catherine.pasquier@meuse.gouv.fr",
                "sophie.barbet@landes.gouv.fr",
                "corinne.loubere@landes.gouv.fr",
                "laure.delerce@landes.gouv.fr",
                "sophie.batifoulier@landes.gouv.fr",
                "isabelle.plagnes@sfr.fr",
                "romain.gaeta@loire-atlantique.gouv.fr",
                "Olivier.claireau@sfr.fr",
                "franck.menard@loire-atlantique.gouv.fr",
                "veronique.laune@loire-atlantique.gouv.fr",
                "ddtm-vserp@loire-atlantique.gouv.fr",
                "thierry.mocogni@eure-et-loir.gouv.fr",
                "isabelle.desile@eure-et-loir.gouv.fr",
                "odile.gomme@eure-et-loir.gouv.fr",
                "jean-philippe.renard@eure-et-loir.gouv.fr",
                "sandra.tachat@eure-et-loir.gouv.fr",
                "philippejos09@hotmail.fr",
                "lilimag.29@gmail.com",
                "construction.durable82@gmail.com",
                "rivagali@hotmail.com",
                "nathalie.cauleur@saone-et-loire.gouv.fr",
                "lucie.pagat@saone-et-loire.gouv.fr",
                "jerome.laville@saone-et-loire.gouv.fr",
                "didier.bonnefoy@saone-et-loire.gouv.fr",
                "axel.schalk@saone-et-loire.gouv.fr",
                "colette.py@haut-rhin.gouv.fr",
                "isabelle.pla@haut-rhin.gouv.fr",
                "danielle.guillaume@haut-rhin.gouv.fr",
                "patrick.reibel@haut-rhin.gouv.fr",
                "stparfait18@hotmail.fr",
                "zohra.benzaghou@jura.gouv.fr",
                "emilie.gauthier@jura.gouv.fr",
                "franck.villet@jura.gouv.fr",
                "thomas.brante@jura.gouv.fr",
                "olivier.decharriere@jura.gouv.fr",
                "max.palix@ardeche.gouv.fr",
                "nathalie.chauvin@ardeche.gouv.fr",
                "mireille.gay@ardeche.gouv.fr",
                "valerie.lafont@ardeche.gouv.fr",
                "magali.aubert@ardeche.gouv.fr",
                "sebastien.charles@marne.gouv.fr",
                "francois-xavier.bouilleret@marne.gouv.fr",
                "jean-michel.demorat@marne.gouv.fr",
                "piero.osti@marne.gouv.fr",
                "damien.thomassin@ain.gouv.fr",
                "fabienne.olivier@ain.gouv.fr",
                "yahya.ettoubi@ain.gouv.fr",
                "daniel.clerc@ain.gouv.fr",
                "sebastien.guichon@ain.gouv.fr",
                "sarah.debrabant@rhone.gouv.fr",
                "barbara.bonelli@rhone.gouv.fr",
                "sylvie.chanut@rhone.gouv.fr",
                "claire.vancauwemberge@rhone.gouv.fr",
                "thierry.morel@rhone.gouv.fr",
                "claire.para-desthomas@haute-savoie.gouv.fr",
            ]
        elif self.nom == "Challenge de l’été beta.gouv":
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
        verbose_name="Joueur",
        on_delete=models.PROTECT,
        related_name="inscriptions",
    )
    challenge = models.ForeignKey(
        "stats.Challenge",
        verbose_name="Challenge",
        on_delete=models.PROTECT,
        related_name="inscriptions",
    )
    inscription_date = models.DateTimeField(verbose_name="Date d'inscription", auto_now_add=True)

    class Meta:
        ordering = ("inscription_date",)
        verbose_name = "Challenge Player"
        verbose_name_plural = "Challenges Players"

    def __str__(self):
        return f"{self.player} - {self.challenge}"


class Referer(models.Model):
    domain = models.URLField(help_text="Domaine du site réutilisateur", unique=True)

    date_notification_to_mattermost = models.DateTimeField(
        null=True, verbose_name="Date de notification sur Mattermost ?"
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "Site réutilisateur"
        verbose_name_plural = "Sites réutilisateur"
        indexes = [
            models.Index(fields=["domain"], name="domain_idx"),
        ]

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
    referer = models.ForeignKey(Referer, on_delete=models.CASCADE, related_name="implementations")
    urlpath = models.URLField(help_text="Url complète", unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de détection de tracking")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de dernier contact")

    class Meta:
        ordering = ("-updated_at", "urlpath")
        verbose_name = "Implémentation du Widget"
        verbose_name_plural = "Implémentations du Widget"
        indexes = [
            models.Index(fields=["referer"], name="referer_idx"),
            models.Index(fields=["urlpath"], name="urlpath_idx"),
        ]

    def __str__(self):
        return self.urlpath
