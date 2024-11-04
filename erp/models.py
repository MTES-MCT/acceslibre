import json
import uuid
from datetime import datetime

import reversion
from autoslug import AutoSlugField
from deepl import QuotaExceededException
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext as translate
from django.utils.translation import gettext_lazy as translate_lazy
from django.utils.translation import ngettext
from reversion.models import Version

from compte.service import increment_nb_erp_administrator, increment_nb_erp_created, increment_nb_erp_edited
from core.lib import diff as diffutils
from core.lib import geo
from erp import managers, schema
from erp.provider import deepl as deepl_provider
from erp.provider import sirene
from erp.provider.departements import DEPARTEMENTS
from subscription.models import ErpSubscription

from .exceptions import MergeException

FULLTEXT_CONFIG = "french_unaccent"

models.CharField.register_lookup(Lower)


def _get_history(versions, exclude_fields=None, exclude_changes_from=None):
    """
    param versions : Queryset de django_reversion.Version

    return history : Liste de dict.
    """
    exclude_fields = exclude_fields if exclude_fields is not None else ()
    history = []
    current_fields_dict = {}
    for version in versions:
        try:
            fields = version.field_dict
        except Exception:
            continue
        else:
            diff = diffutils.dict_diff_keys(current_fields_dict, fields)
        final_diff = []
        for entry in diff:
            entry["label"] = str(schema.get_label(entry["field"], entry["field"]))
            try:
                entry["old"] = str(schema.get_human_readable_value(entry["field"], entry["old"]))
                entry["new"] = str(schema.get_human_readable_value(entry["field"], entry["new"]))
            except NotImplementedError:
                continue
            if entry["old"] != entry["new"]:
                final_diff.append(entry)
        if final_diff and version.revision.user:
            history.insert(
                0,
                {
                    "user": version.revision.user,
                    "date": version.revision.date_created,
                    "comment": version.revision.get_comment(),
                    "diff": [entry for entry in final_diff if entry["field"] not in exclude_fields],
                    "revision": version.revision,
                },
            )
        current_fields_dict = fields
    history = list(filter(lambda x: x["diff"] != [], history))
    if exclude_changes_from:
        history = [entry for entry in history if entry["user"] != exclude_changes_from]
    return history


def get_last_position():
    qs = Activite.objects.order_by("position").exclude(slug=Activite.SLUG_MISCELLANEOUS)
    if qs.exists():
        try:
            return qs.last().position + 1
        except Exception:
            return 1
    return 1


class Activite(models.Model):
    SLUG_MISCELLANEOUS = "autre"

    class Meta:
        ordering = ("nom",)
        verbose_name = translate_lazy("Activité")
        verbose_name_plural = translate_lazy("Activités")
        indexes = [
            models.Index(fields=["slug"]),
        ]

    objects = managers.ActiviteQuerySet.as_manager()

    nom = models.CharField(
        max_length=255, unique=True, verbose_name=translate_lazy("Nom"), help_text=translate_lazy("Nom de l'activité")
    )
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        verbose_name=translate_lazy("Identifiant d'URL (slug)"),
        help_text=translate_lazy("Identifiant d'URL (slug)"),
    )
    mots_cles = ArrayField(
        models.CharField(max_length=40, blank=True),
        verbose_name=translate_lazy("Mots-clés"),
        default=list,
        null=True,
        blank=True,
        help_text=translate_lazy("Liste de mots-clés apparentés à cette activité"),
    )
    naf_ape_code = ArrayField(
        models.CharField(max_length=10),
        verbose_name=translate_lazy("Code NAF/APE"),
        default=list,
        null=True,
        blank=True,
        help_text=translate_lazy("Liste des codes NAF/APE liés à cette activité"),
    )
    icon = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Icône"),
        help_text=mark_safe(
            translate_lazy("Chemin de l'icône ")
            + '<a href="http://www.sjjb.co.uk/mapicons/contactsheet" target="_blank">SSJB</a> '
            "(ex. <code>sport_motorracing</code>)"
        ),
    )
    vector_icon = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        default="building",
        verbose_name=translate_lazy("Icône vectorielle"),
        help_text=mark_safe(
            translate_lazy("Nom de l'icône dans")
            + '<a href="/mapicons" target="_blank">'
            + translate_lazy("le catalogue")
            + "</a>."
        ),
    )
    position = models.PositiveSmallIntegerField(
        default=get_last_position,
        verbose_name=translate_lazy("Position dans la liste"),
    )

    # datetimes
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))

    def __str__(self):
        return self.nom

    @classmethod
    def reorder(cls):
        position = 1
        for act in cls.objects.all().order_by("nom").exclude(slug=Activite.SLUG_MISCELLANEOUS):
            act.position = position
            position += 1
            act.save()

    @property
    def keyword_with_name(self):
        return [self.nom, *self.mots_cles]


class ActivitiesGroup(models.Model):
    name = models.CharField(
        max_length=255, verbose_name=translate_lazy("Nom"), help_text=translate_lazy("Nom du groupe d'activités")
    )
    activities = models.ManyToManyField(Activite, related_name="groups")

    def __str__(self):
        return translate(f"Groupe d'activités : {self.name}")


class ActivitySuggestion(models.Model):
    erp = models.ForeignKey("Erp", verbose_name=translate_lazy("Établissement"), on_delete=models.CASCADE)
    name = models.CharField(max_length=255, help_text=translate_lazy("Nom suggéré pour l'activité"))
    mapped_activity = models.ForeignKey(
        "Activite", verbose_name=translate_lazy("Activité attribuée"), on_delete=models.CASCADE, blank=True, null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=translate_lazy("Utilisateur"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))

    def __str__(self):
        return translate(f"Suggestion d'activité : {self.name}")

    class Meta:
        verbose_name = translate_lazy("Suggestion d'activité")
        verbose_name_plural = translate_lazy("Suggestions d'activités")

    def save(self, *args, **kwargs):
        if self.mapped_activity and self.erp.activite and self.erp.activite.slug == "autre":
            self.erp.activite = self.mapped_activity
            self.erp.save()

        return super().save(*args, **kwargs)


def generate_commune_slug(instance):
    return f"{instance.departement}-{instance.nom}"


class Commune(models.Model):
    class Meta:
        ordering = ("nom",)
        indexes = [
            models.Index(fields=["nom"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["code_insee"]),
            models.Index(fields=["departement"]),
            models.Index(fields=["nom", "departement"]),
            models.Index(fields=["nom", "code_postaux"]),
            models.Index(fields=["arrondissement"]),
            models.Index(fields=["obsolete"]),
            models.Index(fields=["obsolete", "arrondissement"]),
        ]

    objects = managers.CommuneQuerySet.as_manager()

    nom = models.CharField(max_length=255, help_text=translate_lazy("Nom"))
    slug = AutoSlugField(
        unique=True,
        populate_from=generate_commune_slug,
        unique_with=["departement", "nom"],
        help_text=translate_lazy("Identifiant d'URL (slug)"),
    )
    departement = models.CharField(
        max_length=3,
        verbose_name=translate_lazy("Département"),
        help_text=translate_lazy("Codé sur deux ou trois caractères."),
    )
    code_insee = models.CharField(
        max_length=5,
        verbose_name=translate_lazy("Code INSEE"),
        help_text=translate_lazy("Code INSEE de la commune"),
    )
    superficie = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Superficie"),
        help_text=translate_lazy("Exprimée en hectares (ha)"),
    )
    population = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Population"),
        help_text=translate_lazy("Nombre d'habitants estimé"),
    )
    geom = models.PointField(
        verbose_name=translate_lazy("Localisation"),
        help_text=translate_lazy("Coordonnées géographiques du centre de la commune"),
    )
    contour = models.MultiPolygonField(
        verbose_name=translate_lazy("Contour"),
        help_text=translate_lazy("Contour de la commune"),
        null=True,
    )
    code_postaux = ArrayField(
        models.CharField(max_length=5),
        verbose_name=translate_lazy("Codes postaux"),
        default=list,
        help_text=translate_lazy("Liste des codes postaux de cette commune"),
    )
    arrondissement = models.BooleanField(
        verbose_name=translate_lazy("Arrondissement"),
        default=False,
        help_text=translate_lazy("Cette commune est un arrondissement (Paris, Lyon, Marseille)"),
    )
    obsolete = models.BooleanField(
        verbose_name=translate_lazy("Obsolète"),
        default=False,
        help_text=translate_lazy("La commune est obsolète, par exemple suite à un regroupement ou un rattachement"),
    )

    def __str__(self):
        return f"{self.nom} ({self.departement})"

    def get_absolute_url(self):
        return reverse("search_commune", kwargs={"commune_slug": self.slug})

    def clean(self):
        if self.arrondissement is True and self.departement not in ["13", "69", "75"]:
            raise ValidationError(
                {"arrondissement": translate("Seules Paris, Lyon et Marseille peuvent disposer d'arrondissements")}
            )

    def departement_nom(self):
        nom = DEPARTEMENTS.get(self.departement, {}).get("nom")
        return f"{nom} ({self.departement})"

    def get_zoom(self):
        if not self.superficie or self.superficie > 8000:
            return settings.MAP_DEFAULT_ZOOM_LARGE_CITY
        elif self.superficie > 6000:
            return 13
        return 14

    def toTemplateJson(self):
        return json.dumps(
            {
                "nom": self.nom,
                "slug": self.slug,
                "center": geo.lonlat_to_latlon(self.geom.coords),
                "contour": geo.lonlat_to_latlon(self.contour.coords) if self.contour else None,
                "zoom": self.get_zoom(),
            }
        )


class ExternalSource(models.Model):
    SOURCE_ACCESLIBRE = "acceslibre"
    SOURCE_ACCEO = "acceo"
    SOURCE_ADMIN = "admin"
    SOURCE_API = "api"
    SOURCE_API_ENTREPRISE = "entreprise_api"
    SOURCE_CCONFORME = "cconforme"
    SOURCE_GENDARMERIE = "gendarmerie"
    SOURCE_LORIENT = "lorient"
    SOURCE_NESTENN = "nestenn"
    SOURCE_ODS = "opendatasoft"
    SOURCE_PUBLIC = "public"
    SOURCE_PUBLIC_ERP = "public_erp"
    SOURCE_SAP = "sap"
    SOURCE_SERVICE_PUBLIC = "service_public"
    SOURCE_SIRENE = "sirene"
    SOURCE_TH = "tourisme-handicap"
    SOURCE_TYPEFORM = "typeform"
    SOURCE_TYPEFORM_MUSEE = "typeform_musee"
    SOURCE_VACCINATION = "centres-vaccination"
    SOURCE_DELL = "dell"
    SOURCE_OUTSCRAPER = "outscraper"
    SOURCE_SCRAPFLY = "scrapfly"
    SOURCE_SCRAPFLY2 = "scrapfly2"
    SOURCE_TALLY = "tally"
    SOURCE_LAPOSTE = "laposte"
    SOURCE_CHOICES = (
        (SOURCE_ACCESLIBRE, translate_lazy("Base de données Acceslibre")),
        (SOURCE_ACCEO, translate_lazy("Acceo")),
        (SOURCE_ADMIN, translate_lazy("Back-office")),
        (SOURCE_API, translate_lazy("API")),
        (SOURCE_API_ENTREPRISE, translate_lazy("API Entreprise (publique)")),
        (SOURCE_CCONFORME, translate_lazy("cconforme")),
        (SOURCE_GENDARMERIE, translate_lazy("Gendarmerie")),
        (SOURCE_LORIENT, translate_lazy("Lorient")),
        (SOURCE_NESTENN, translate_lazy("Nestenn")),
        (SOURCE_ODS, translate_lazy("API OpenDataSoft")),
        (SOURCE_PUBLIC, translate_lazy("Saisie manuelle publique")),
        (SOURCE_PUBLIC_ERP, translate_lazy("API des établissements publics")),
        (SOURCE_SAP, translate_lazy("Sortir À Paris")),
        (SOURCE_SERVICE_PUBLIC, translate_lazy("Service Public")),
        (SOURCE_SIRENE, translate_lazy("API Sirene INSEE")),
        (SOURCE_TH, translate_lazy("Tourisme & Handicap")),
        (SOURCE_TYPEFORM, translate_lazy("Questionnaires Typeform")),
        (SOURCE_TYPEFORM_MUSEE, translate_lazy("Questionnaires Typeform Musée")),
        (SOURCE_VACCINATION, translate_lazy("Centres de vaccination")),
        (SOURCE_DELL, translate_lazy("Dell")),
        (SOURCE_OUTSCRAPER, translate_lazy("Outscraper")),
        (SOURCE_SCRAPFLY, translate_lazy("Scrapfly")),
        (SOURCE_SCRAPFLY2, translate_lazy("Scrapfly2")),
        (SOURCE_TALLY, translate_lazy("Tally")),
        (SOURCE_LAPOSTE, translate_lazy("La Poste")),
    )

    erp = models.ForeignKey(
        "Erp", verbose_name=translate_lazy("Établissement"), on_delete=models.CASCADE, related_name="sources"
    )
    source = models.CharField(
        max_length=100,
        null=True,
        verbose_name=translate_lazy("Source"),
        default=SOURCE_PUBLIC,
        choices=SOURCE_CHOICES,
        help_text=translate_lazy("Nom de la source de données dont est issu cet ERP"),
    )
    source_id = models.CharField(max_length=64, help_text=translate_lazy("Identifiant externe de cet ERP"))

    unique_together = {("source", "erp")}

    def __str__(self):
        return translate(f"Source externe pour ERP#{self.erp_id} sur {self.source} avec id {self.source_id}")


@reversion.register(
    ignore_duplicates=True,
    exclude=[
        "id",
        "uuid",
        "source",
        "source_id",
        "search_vector",
    ],
)
class Erp(models.Model):
    HISTORY_MAX_LATEST_ITEMS = 25  # Fix me : move to settings

    USER_ROLE_ADMIN = "admin"
    USER_ROLE_GESTIONNAIRE = "gestionnaire"
    USER_ROLE_PUBLIC = "public"
    USER_ROLE_SYSTEM = "system"
    USER_ROLES = (
        (USER_ROLE_ADMIN, translate_lazy("Administration")),
        (USER_ROLE_GESTIONNAIRE, translate_lazy("Gestionnaire")),
        (USER_ROLE_PUBLIC, translate_lazy("Utilisateur public")),
        (USER_ROLE_SYSTEM, translate_lazy("Système")),
    )

    class Meta:
        ordering = ("nom",)
        verbose_name = translate_lazy("Établissement")
        verbose_name_plural = translate_lazy("Établissements")
        indexes = [
            models.Index(fields=["nom"]),
            models.Index(fields=["source", "source_id"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["commune"]),
            models.Index(fields=["commune", "activite_id"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["published", "geom"]),  # used in many managers
            GinIndex(name="nom_trgm", fields=["nom"], opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["search_vector"]),
            GinIndex(fields=["metadata"], name="gin_metadata"),
        ]
        constraints = [
            UniqueConstraint(
                fields=["asp_id"],
                name="unique_asp_id_published",
                condition=(Q(published=True) & Q(asp_id__isnull=False) & ~Q(asp_id="")),
            ),
        ]

    objects = managers.ErpQuerySet.as_manager()

    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    # FIXME to be deprecated, will be dropped once all data will be stored on ExternalSource and all usages removed.
    source = models.CharField(
        max_length=100,
        null=True,
        verbose_name=translate_lazy("Source"),
        default=ExternalSource.SOURCE_PUBLIC,
        choices=ExternalSource.SOURCE_CHOICES,
        help_text=translate_lazy("Nom de la source de données dont est issu cet ERP"),
    )
    source_id = models.CharField(
        max_length=255,
        null=True,
        verbose_name=translate_lazy("Source ID"),
        help_text=translate_lazy("Identifiant de l'ERP dans la source initiale de données"),
    )
    asp_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("ASP ID"),
        help_text=translate_lazy("Identifiant de l'ERP dans la base Service Public"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name=translate_lazy("Contributeur"),
        on_delete=models.SET_NULL,
    )
    user_type = models.CharField(
        max_length=50,
        choices=USER_ROLES,
        verbose_name=translate_lazy("Profil de contributeur"),
        default=USER_ROLE_SYSTEM,
    )

    commune_ext = models.ForeignKey(
        Commune,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Commune (relation)"),
        help_text=translate_lazy("La commune de cet établissement"),
        on_delete=models.SET_NULL,
    )
    nom = models.CharField(
        max_length=255,
        verbose_name=translate_lazy("Nom"),
        help_text=translate_lazy("Nom de l'établissement ou de l'enseigne"),
    )
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text=translate_lazy("Identifiant d'URL (slug)"),
        verbose_name=translate_lazy("Identifiant d'URL (slug)"),
        max_length=255,
    )
    activite = models.ForeignKey(
        Activite,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Activité"),
        help_text=translate_lazy(
            "Domaine d'activité de l'ERP. Attention, la recherche se fait sur les lettres accentuées"
        ),
        on_delete=models.SET_NULL,
    )
    published = models.BooleanField(
        default=True,
        verbose_name=translate_lazy("Publié"),
        help_text=translate_lazy(
            "Statut de publication de cet ERP: si la case est décochée, l'ERP ne sera pas listé publiquement"
        ),
    )
    geom = models.PointField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Localisation"),
        help_text=translate_lazy("Géolocalisation (carte rafraîchie une fois l'enregistrement sauvegardé)"),
    )
    geoloc_provider = models.CharField(
        default=None,
        blank=True,
        null=True,
        max_length=50,
        verbose_name=translate_lazy("Fournisseur utilisé pour la géolocalisation"),
        help_text=translate_lazy("Indique le fournisseur utilisé pour la géolocalisation de l'adresse de l'ERP."),
    )
    siret = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        verbose_name=translate_lazy("SIRET"),
        help_text=translate_lazy("Numéro SIRET si l'ERP est une entreprise"),
    )
    # contact
    telephone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Téléphone"),
        help_text=translate_lazy("Numéro de téléphone de l'ERP"),
    )
    site_internet = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Site internet"),
        help_text=translate_lazy("Adresse du site internet de l'ERP"),
    )
    contact_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Courriel"),
        help_text=translate_lazy("Adresse email permettant de contacter l'ERP"),
    )
    contact_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Lien vers outil de contact"),
        help_text=translate_lazy("Lien hypertexte permettant de contacter l'établissement (formulaire, chatbot, etc.)"),
    )
    # adresse
    numero = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Numéro"),
        help_text=translate_lazy("Numéro dans la voie, incluant le complément (BIS, TER, etc.)"),
    )
    voie = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=translate_lazy("Voie"),
        verbose_name=translate_lazy("Voie"),
    )
    lieu_dit = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=translate_lazy("Lieu dit"),
        verbose_name=translate_lazy("Lieu dit"),
    )
    code_postal = models.CharField(
        max_length=5,
        help_text=translate_lazy("Code postal"),
        verbose_name=translate_lazy("Code postal"),
    )
    commune = models.CharField(
        max_length=255,
        help_text=translate_lazy("Nom de la commune"),
        verbose_name=translate_lazy("Commune"),
    )
    code_insee = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Code INSEE"),
        help_text=translate_lazy("Code INSEE de la commune"),
    )
    ban_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=translate_lazy("identifiant BAN"),
        help_text=translate_lazy("Identifiant de la BAN"),
    )

    # Metadata
    # Notes:
    # - DO NOT store Python datetimes or attempt to pass some; JSON doesn't
    # have a native datetime type, so while we could encode dates, we couldn't
    # reliably decode them
    # - For updating nested values, you have to retrieve the whole object,
    # update the target nested values so the metadata object is mutated, then
    # save the instance. See tests for illustration.
    # XXX: we might want to provide convenient getter and setters targetting
    # given nested keys later at some point.
    metadata = models.JSONField(default=dict)

    # datetimes
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))
    checked_up_to_date_at = models.DateTimeField(
        null=True, blank=True, verbose_name=translate_lazy("Dernière vérification des informations")
    )
    check_closed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=translate_lazy("Dernière vérification de clôture")
    )
    permanently_closed = models.BooleanField(
        default=False,
        verbose_name=translate_lazy("Définitivement clos"),
        help_text=translate_lazy(
            "Statut de fermeture de cet ERP: si la case est cochée, l'ERP est définitivement clos et ne peut pas être inséré à nouveau."
        ),
    )

    # search vector
    search_vector = SearchVectorField(translate_lazy("Search vector"), null=True)

    import_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Email lié à l'import"),
        help_text=translate_lazy("Adresse email permettant de relancer l'utilisateur lié à l'import de l'ERP"),
    )

    __original_activite_id = None
    __original_user_id = None
    __original_user_type = None
    __original_source_id = None
    __confirmation_message = "Created via confirmation button"

    def __str__(self):
        return f"ERP #{self.id} ({self.nom}, {self.commune}, {self.slug})"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_activite_id = self.activite_id
        self.__original_user_id = self.user_id
        self.__original_user_type = self.user_type

    def get_activite_vector_icon(self):
        default = "building"
        if self.activite and self.activite.vector_icon:
            return self.activite.vector_icon
        return default

    def get_first_user(self):
        user_list = [version["user"] for version in self.get_history() if version["user"] is not None]
        if user_list:
            return user_list[-1]

    def get_history(self, exclude_changes_from=None):
        "Combines erp and related accessibilite histories."
        erp_history = _get_history(
            self.get_versions(),
            exclude_fields=(
                "uuid",
                "source",
                "source_id",
                "search_vector",
                "updated_at",
                "created_at",
            ),
            exclude_changes_from=exclude_changes_from,
        )
        accessibilite_history = self.accessibilite.get_history(exclude_changes_from=exclude_changes_from)
        global_history = erp_history + accessibilite_history
        global_history.sort(key=lambda x: x["date"], reverse=True)
        return global_history

    def get_versions(self):
        # take the last n revisions
        qs = (
            Version.objects.get_for_object(self)
            .select_related("revision__user")
            .order_by("-revision__date_created")[: self.HISTORY_MAX_LATEST_ITEMS + 1]
        )

        # make it a list, so it's reversable
        versions = list(qs)
        # reorder the slice by date_created ASC
        versions.reverse()
        return versions

    def editable_by(self, user):
        if not user.is_active:
            return False
        # admins can do whatever they want
        if user.is_superuser:
            return True
        # intrapreneurs can update any erps
        if "intrapreneurs" in list(user.groups.values_list("name")):
            return True
        # users can take over erps with no owner
        if not self.user:
            return True
        # check ownership
        if user.id != self.user.id:
            return False
        return True

    def get_absolute_uri(self):
        return f"{settings.SITE_ROOT_URL}{self.get_absolute_url()}"

    def get_success_url(self):
        return f"{self.get_absolute_url()}?success=true"

    def get_absolute_url(self):
        commune_slug = self.commune_ext.slug if self.commune_ext else slugify(f"{self.departement}-{self.commune}")
        if self.activite is None:
            return reverse(
                "commune_erp",
                kwargs=dict(commune=commune_slug, erp_slug=self.slug),
            )
        else:
            return reverse(
                "commune_activite_erp",
                kwargs=dict(
                    commune=commune_slug,
                    activite_slug=self.activite.slug,
                    erp_slug=self.slug,
                ),
            )

    def get_admin_url(self):
        return reverse("admin:erp_erp_change", kwargs={"object_id": self.pk}) if self.pk else None

    def get_global_timestamps(self):
        created_at = self.created_at
        updated_at = self.created_at
        if self.has_accessibilite():
            history = self.accessibilite.get_history()
            a_updated_at = history[0]["date"] if history else self.accessibilite.created_at
            updated_at = max(a_updated_at, self.created_at)
            created_at = max(self.accessibilite.created_at, self.created_at)
        return {
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def has_accessibilite(self):
        return hasattr(self, "accessibilite") and self.accessibilite is not None

    def is_subscribed_by(self, user):
        return ErpSubscription.objects.filter(user=user, erp=self).count() == 1

    @property
    def adresse(self):
        pieces = [
            str(x)
            for x in [
                self.numero,
                self.voie,
                self.lieu_dit,
                self.code_postal,
                self.commune,
            ]
            if x is not None
        ]
        return " ".join(pieces).strip().replace("  ", " ")

    @property
    def short_adresse(self):
        pieces = [
            str(x)
            for x in [
                self.numero,
                self.voie,
                self.lieu_dit,
            ]
            if x is not None
        ]
        return " ".join(pieces).strip().replace("  ", " ")

    @property
    def departement(self):
        if self.code_postal[:3] in ("971", "972", "973", "974", "975", "976", "978", "986", "987", "988"):
            return self.code_postal[:3]

        return self.code_postal[:2]

    def clean(self):  # Fix me : move to form (abstract)
        # Code postal
        if self.code_postal and len(self.code_postal) != 5:
            raise ValidationError({"code_postal": translate("Le code postal doit faire 5 caractères")})

        # Voie OU lieu-dit sont requis
        if self.voie is None and self.lieu_dit is None:
            error = translate("Veuillez entrer une voie ou un lieu-dit")
            raise ValidationError({"voie": error, "lieu_dit": error})

        # Commune
        if self.commune and self.code_postal:
            matches = Commune.objects.filter(
                nom__unaccent__iexact=self.commune,
                code_postaux__contains=[self.code_postal],
            )
            if not matches:
                matches = Commune.objects.filter(code_postaux__contains=[self.code_postal])
            if not matches:
                matches = Commune.objects.filter(code_insee=self.code_insee)
            if not matches:
                matches = Commune.objects.filter(
                    nom__unaccent__iexact=self.commune,
                )
            if not matches:
                raise ValidationError(
                    {"commune": translate(f"Commune {self.commune} introuvable, veuillez vérifier votre saisie.")}
                )

            self.commune_ext = matches[0]

        # SIRET
        if self.siret:
            siret = sirene.validate_siret(self.siret)
            if siret is None:
                raise ValidationError({"siret": translate("Ce numéro SIRET est invalide.")})
            self.siret = siret

    def _increment_stats(self, editor=None):
        if self.pk:
            if self.__original_user_id is None:
                if self.user:
                    # ERP has just been attributed to a user, manage his user_stats
                    increment_nb_erp_created(self.user)
            elif editor:
                increment_nb_erp_edited(editor)

            if self.__original_user_type != self.user_type and self.user_type == self.USER_ROLE_GESTIONNAIRE:
                # ERP has just been changed to user_type=GESTIONNAIRE
                increment_nb_erp_administrator(self.user)

        elif self.user:
            increment_nb_erp_created(self.user)
            if self.user_type == self.USER_ROLE_GESTIONNAIRE:
                increment_nb_erp_administrator(self.user)

    def save(self, *args, editor=None, **kwargs):
        if editor and not self.user:
            self.user = editor

        if self.permanently_closed:
            self.published = False

        self._increment_stats(editor)

        if (
            self.__original_activite_id is not None
            and self.activite_id != self.__original_activite_id
            and self.has_accessibilite()
        ):
            # We wipe conditional questions' answer only if the new activity is in a distinct activity group.
            # We could have stored an ___original_group_activity_id but it would have create overload on each __init__
            # by fetching a joined attribute.
            group_activity_has_changed = False
            try:
                original_activite = Activite.objects.get(pk=self.__original_activite_id)
            except Activite.DoesNotExist:
                pass

            if not (original_groups := original_activite.groups.all()):
                group_activity_has_changed = True
            else:
                group_activity_has_changed = self.activite_id not in [
                    a.pk for g in original_groups.all() for a in g.activities.all()
                ]

            if group_activity_has_changed:
                accessibility = self.accessibilite
                for field in schema.get_conditional_fields():
                    setattr(accessibility, field, None)
                accessibility.save()

        search_vector = SearchVector(
            Value(self.nom, output_field=models.TextField()),
            weight="A",
            config=FULLTEXT_CONFIG,
        )
        if self.activite is not None:
            search_vector = search_vector + SearchVector(
                Value(
                    self.activite.nom,
                    output_field=models.TextField(),
                ),
                weight="A",
                config=FULLTEXT_CONFIG,
            )
            if self.activite.mots_cles is not None:
                search_vector = search_vector + SearchVector(
                    Value(
                        " ".join(self.activite.mots_cles),
                        output_field=models.TextField(),
                    ),
                    weight="B",
                    config=FULLTEXT_CONFIG,
                )
        self.search_vector = search_vector
        super().save(*args, **kwargs)

    def translate(self, target_lang: str):
        if target_lang == settings.LANGUAGE_CODE or not self.has_accessibilite():
            return self

        access = self.accessibilite
        fields_to_translate = schema.get_free_text_fields()
        for field_to_translate in fields_to_translate:
            if field_value := getattr(access, field_to_translate, None):
                try:
                    setattr(self.accessibilite, field_to_translate, deepl_provider.translate(field_value, target_lang))
                except QuotaExceededException:
                    return self  # We won't be able to translate anymore, keep it in french
        return self

    @property
    def has_miscellaneous_activity(self):
        return self.activite.slug == Activite.SLUG_MISCELLANEOUS

    def shares_same_accessibility_data_with(self, other_erps):
        if not self.has_accessibilite():
            return False
        if not all([e.has_accessibilite for e in other_erps]):
            return False

        return all([self.accessibilite == e.accessibilite for e in other_erps])

    @property
    def is_human_source(self):
        return bool(
            self.source == ExternalSource.SOURCE_PUBLIC
            or self.user
            or (self.import_email and not self.source == ExternalSource.SOURCE_SERVICE_PUBLIC)
        )

    @property
    def was_created_by_business_owner(self):
        return self.user_type == self.USER_ROLE_GESTIONNAIRE

    @property
    def was_created_by_administration(self):
        return self.user_type == self.USER_ROLE_ADMIN

    @property
    def is_cultural_place(self):
        return self.activite.groups.filter(name="Lieux culturels").exists()

    @property
    def is_accommodation(self):
        return self.activite.groups.filter(name="Hébergement").exists()

    def merge_accessibility_with(self, erp, fields=None):
        access_destination = self.accessibilite
        access_source = erp.accessibilite

        if fields is None:
            fields = list(schema.FIELDS.keys())
            fields.remove("activite")

        needs_save = False
        for field in fields:
            a_field = getattr(access_source, field)
            b_field = getattr(access_destination, field)
            if a_field != b_field:
                if a_field is not None and b_field in (None, [], ""):
                    setattr(access_destination, field, a_field)
                    needs_save = True
                elif b_field is not None and a_field in (None, [], ""):
                    setattr(access_destination, field, b_field)
                    needs_save = True
                else:
                    raise MergeException(
                        f"Can't merge ERP {self.pk} with ERP {erp.pk}, field {field} has value {a_field} and {b_field}"
                    )

        if needs_save:
            access_destination.save()

    @property
    def displayed_last_updated_date(self):
        dates = [d for d in [self.checked_up_to_date_at, self.created_at, self.updated_at] if d]
        if dates:
            return max(dates)

    def confirm_up_to_date(self, user):
        self.checked_up_to_date_at = datetime.now()
        with reversion.create_revision():
            self.save()
            reversion.set_comment(self.__confirmation_message)
            if isinstance(user, get_user_model()):
                reversion.set_user(user)


@reversion.register(
    ignore_duplicates=True,
    exclude=[
        "id",
        "erp_id",
        "completion_rate",
    ],
)
class Accessibilite(models.Model):
    HISTORY_MAX_LATEST_ITEMS = 25

    class Meta:
        verbose_name = translate_lazy("Accessibilité")
        verbose_name_plural = translate_lazy("Accessibilité")

        # To understand why we are using Q(field=True) & Q(field__isnull=False), see https://code.djangoproject.com/ticket/33595
        constraints = [
            CheckConstraint(
                name="%(app_label)s_%(class)s_transport_consistency",
                check=(
                    (Q(transport_station_presence=True) & Q(transport_station_presence__isnull=False))
                    | (Q(transport_information="") | Q(transport_information__isnull=True))
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_stationnement_consistency",
                check=(
                    (Q(stationnement_presence=True) & Q(stationnement_presence__isnull=False))
                    | Q(stationnement_pmr=None)
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_stationnement_ext_consistency",
                check=(
                    (Q(stationnement_ext_presence=True) & Q(stationnement_ext_presence__isnull=False))
                    | Q(stationnement_ext_pmr=None)
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_cheminement_ext_plain_pied_consistency",
                check=(
                    (Q(cheminement_ext_plain_pied=False) & Q(cheminement_ext_plain_pied__isnull=False))
                    | (
                        Q(cheminement_ext_ascenseur=None)
                        & Q(cheminement_ext_nombre_marches__isnull=True)
                        & Q(cheminement_ext_sens_marches__isnull=True)
                        & Q(cheminement_ext_reperage_marches__isnull=True)
                        & Q(cheminement_ext_main_courante__isnull=True)
                        & Q(cheminement_ext_rampe__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_cheminement_ext_pente_consistency",
                check=(
                    (Q(cheminement_ext_pente_presence=True) & Q(cheminement_ext_pente_presence__isnull=False))
                    | (
                        Q(cheminement_ext_pente_degre_difficulte__isnull=True)
                        & Q(cheminement_ext_pente_longueur__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_cheminement_ext_presence_consistency",
                check=(
                    (Q(cheminement_ext_presence=True) & Q(cheminement_ext_presence__isnull=False))
                    | (
                        Q(cheminement_ext_terrain_stable__isnull=True)
                        & Q(cheminement_ext_plain_pied__isnull=True)
                        & Q(cheminement_ext_pente_presence__isnull=True)
                        & Q(cheminement_ext_devers__isnull=True)
                        & Q(cheminement_ext_bande_guidage__isnull=True)
                        & Q(cheminement_ext_retrecissement__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_entree_vitree_consistency",
                check=(
                    (Q(entree_vitree=True) & Q(entree_vitree__isnull=False)) | Q(entree_vitree_vitrophanie__isnull=True)
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_entree_porte_presence_consistency",
                check=(
                    (Q(entree_porte_presence=True) & Q(entree_porte_presence__isnull=False))
                    | (
                        Q(entree_porte_manoeuvre__isnull=True)
                        & Q(entree_porte_type__isnull=True)
                        & Q(entree_vitree__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_entree_plain_pied_consistency",
                check=(
                    (Q(entree_plain_pied=False) & Q(entree_plain_pied__isnull=False))
                    | (
                        Q(entree_ascenseur__isnull=True)
                        & (Q(entree_marches__isnull=True) | Q(entree_marches=0))
                        & Q(entree_marches_sens__isnull=True)
                        & Q(entree_marches_reperage__isnull=True)
                        & Q(entree_marches_main_courante__isnull=True)
                        & Q(entree_marches_rampe__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_entree_dispositif_appel_consistency",
                check=(
                    (Q(entree_dispositif_appel=True) & Q(entree_dispositif_appel__isnull=False))
                    | (Q(entree_dispositif_appel_type__isnull=True) | Q(entree_dispositif_appel_type=[]))
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_entree_pmr_consistency",
                check=(
                    (Q(entree_pmr=True) & Q(entree_pmr__isnull=False))
                    | (Q(entree_pmr_informations__isnull=True) | Q(entree_pmr_informations=""))
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_accueil_cheminement_plain_pied_consistency",
                check=(
                    ~Q(accueil_cheminement_plain_pied=True)
                    | (
                        Q(accueil_cheminement_ascenseur__isnull=True)
                        & Q(accueil_cheminement_nombre_marches__isnull=True)
                        & Q(accueil_cheminement_sens_marches__isnull=True)
                        & Q(accueil_cheminement_reperage_marches__isnull=True)
                        & Q(accueil_cheminement_main_courante__isnull=True)
                        & Q(accueil_cheminement_rampe__isnull=True)
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_accueil_audiodescription_consistency",
                check=(
                    (Q(accueil_audiodescription_presence=True) & Q(accueil_audiodescription_presence__isnull=False))
                    | (Q(accueil_audiodescription__isnull=True) | Q(accueil_audiodescription=[]))
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_accueil_equipements_malentendants_consistency",
                check=(
                    (
                        Q(accueil_equipements_malentendants_presence=True)
                        & Q(accueil_equipements_malentendants_presence__isnull=False)
                    )
                    | (Q(accueil_equipements_malentendants__isnull=True) | Q(accueil_equipements_malentendants=[]))
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_sanitaires_presence_consistency",
                check=(Q(sanitaires_presence=True) & Q(sanitaires_presence__isnull=False)) | Q(sanitaires_adaptes=None),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_labels_consistency",
                check=(
                    ~(Q(labels=[]) | Q(labels__isnull=True))
                    | (
                        (Q(labels_familles_handicap=[]) | Q(labels_familles_handicap__isnull=True))
                        & (Q(labels_autre__isnull=True) | Q(labels_autre=""))
                    )
                ),
            ),
            CheckConstraint(
                name="%(app_label)s_%(class)s_chambre_consistency",
                check=(
                    ~(Q(accueil_chambre_nombre_accessibles=0) | Q(accueil_chambre_nombre_accessibles__isnull=True))
                    | (
                        Q(accueil_chambre_douche_plain_pied__isnull=True)
                        & Q(accueil_chambre_douche_siege__isnull=True)
                        & Q(accueil_chambre_douche_barre_appui__isnull=True)
                        & Q(accueil_chambre_sanitaires_barre_appui__isnull=True)
                        & Q(accueil_chambre_sanitaires_espace_usage__isnull=True)
                    )
                ),
            ),
        ]

    erp = models.OneToOneField(
        Erp,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Établissement"),
        help_text=translate_lazy("ERP"),
    )

    ###################################
    # Transports en commun            #
    ###################################
    # Station de transport en commun
    transport_station_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("transport_station_presence"),
        verbose_name=translate_lazy("Desserte par transports en commun"),
    )
    transport_information = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Informations transports"),
    )

    ###################################
    # Stationnement                   #
    ###################################
    # Stationnement dans l'ERP
    stationnement_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("stationnement_presence"),
        verbose_name=translate_lazy("Stationnement dans l'ERP"),
    )
    stationnement_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("stationnement_pmr"),
        verbose_name=translate_lazy("Stationnements PMR dans l'ERP"),
    )

    # Stationnement à proximité
    stationnement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("stationnement_ext_presence"),
        verbose_name=translate_lazy("Stationnement à proximité de l'ERP"),
    )
    stationnement_ext_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("stationnement_ext_pmr"),
        verbose_name=translate_lazy("Stationnements PMR à proximité de l'ERP"),
    )

    ###################################
    # Espace et Cheminement extérieur #
    ###################################
    cheminement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Espace extérieur"),
    )

    # Cheminement de plain-pied – oui / non / inconnu
    cheminement_ext_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_plain_pied"),
        verbose_name=translate_lazy("Cheminement de plain-pied"),
    )
    # Terrain meuble ou accidenté
    cheminement_ext_terrain_stable = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_terrain_stable"),
        verbose_name=translate_lazy("Terrain meuble ou accidenté"),
    )
    # Nombre de marches – nombre entre 0 et >10
    cheminement_ext_nombre_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Nombre de marches"),
    )
    # Sens des marches de l'escalier
    cheminement_ext_sens_marches = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Sens de circulation de l'escalier"),
        choices=schema.ESCALIER_SENS,
    )
    # Repérage des marches ou de l’escalier – oui / non / inconnu / sans objet
    cheminement_ext_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Repérage des marches ou de l’escalier"),
    )
    # Main courante - oui / non / inconnu / sans objet
    cheminement_ext_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Main courante"),
    )
    # Rampe – aucune / fixe / amovible / sans objet
    cheminement_ext_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=schema.RAMPE_CHOICES,
        verbose_name=translate_lazy("Rampe"),
    )
    # Ascenseur / élévateur : oui / non / inconnu / sans objet
    cheminement_ext_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_ascenseur"),
        verbose_name=translate_lazy("Ascenseur/élévateur"),
    )

    # Pente - oui / non / inconnu
    cheminement_ext_pente_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_pente_presence"),
        verbose_name=translate_lazy("Pente présence"),
    )

    # Pente - Aucune, légère, importante, inconnu
    cheminement_ext_pente_degre_difficulte = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=schema.PENTE_CHOICES,
        verbose_name=translate_lazy("Difficulté de la pente"),
    )

    # Pente - Aucune, légère, importante, inconnu
    cheminement_ext_pente_longueur = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=schema.PENTE_LENGTH_CHOICES,
        verbose_name=translate_lazy("Longueur de la pente"),
    )

    # Dévers - Aucun, léger, important, inconnu
    cheminement_ext_devers = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Dévers"),
        choices=schema.DEVERS_CHOICES,
    )

    # Bande de guidage – oui / non / inconnu
    cheminement_ext_bande_guidage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_bande_guidage"),
        verbose_name=translate_lazy("Bande de guidage"),
    )

    # Rétrécissement du cheminement  – oui / non / inconnu
    cheminement_ext_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("cheminement_ext_retrecissement"),
        verbose_name=translate_lazy("Rétrécissement du cheminement"),
    )

    ##########
    # Entrée #
    ##########
    # Entrée facilement repérable  – oui / non / inconnu
    entree_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Entrée facilement repérable"),
    )

    # Présence d'une porte (oui / non)
    entree_porte_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_porte_presence"),
        verbose_name=translate_lazy("Y a-t-il une porte ?"),
    )
    # Manoeuvre de la porte (porte battante / porte coulissante / tourniquet / porte tambour / inconnu ou sans objet)
    entree_porte_manoeuvre = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=schema.PORTE_MANOEUVRE_CHOICES,
        verbose_name=translate_lazy("Manœuvre de la porte"),
    )
    # Type de porte (manuelle / automatique / inconnu)
    entree_porte_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=schema.PORTE_TYPE_CHOICES,
        verbose_name=translate_lazy("Type de porte"),
    )

    # Entrée vitrée
    entree_vitree = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_vitree"),
        verbose_name=translate_lazy("Entrée vitrée"),
    )
    entree_vitree_vitrophanie = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Vitrophanie"),
    )

    # Entrée de plain-pied
    entree_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_plain_pied"),
        verbose_name=translate_lazy("Entrée de plain-pied"),
    )
    # Nombre de marches
    entree_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Marches d'escalier"),
    )
    # Sens des marches de l'escalier
    entree_marches_sens = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Sens de circulation de l'escalier"),
        choices=schema.ESCALIER_SENS,
    )
    # Repérage des marches ou de l'escalier
    entree_marches_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Repérage de l'escalier"),
    )
    # Main courante
    entree_marches_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Main courante"),
    )
    # Rampe
    entree_marches_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Rampe"),
        choices=schema.RAMPE_CHOICES,
    )
    # Système de guidage sonore  – oui / non / inconnu
    entree_balise_sonore = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_balise_sonore"),
        verbose_name=translate_lazy("Présence d'une balise sonore"),
    )
    # Dispositif d’appel
    entree_dispositif_appel = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_dispositif_appel"),
        verbose_name=translate_lazy("Dispositif d'appel"),
    )
    entree_dispositif_appel_type = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.DISPOSITIFS_APPEL_CHOICES),
        verbose_name=translate_lazy("Dispositifs d'appel disponibles"),
        default=list,
        null=True,
        blank=True,
    )
    entree_aide_humaine = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_aide_humaine"),
        verbose_name=translate_lazy("Aide humaine"),
    )
    entree_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_ascenseur"),
        verbose_name=translate_lazy("Ascenseur/élévateur"),
    )

    # Largeur minimale
    entree_largeur_mini = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Largeur minimale"),
    )

    # Entrée spécifique PMR
    entree_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("entree_pmr"),
        verbose_name=translate_lazy("Entrée spécifique PMR"),
    )

    # Informations sur l’entrée spécifique
    entree_pmr_informations = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Infos entrée spécifique PMR"),
    )

    ###########
    # Accueil #
    ###########
    # Visibilité directe de la zone d'accueil depuis l’entrée
    accueil_visibilite = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_visibilite"),
        verbose_name=translate_lazy("Visibilité directe de la zone d'accueil depuis l'entrée"),
    )

    # Personnel d’accueil
    accueil_personnels = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=schema.PERSONNELS_CHOICES,
        verbose_name=translate_lazy("Personnel d'accueil"),
    )

    # Audiodescription
    accueil_audiodescription_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_audiodescription_presence"),
        verbose_name=translate_lazy("Audiodescription"),
    )
    accueil_audiodescription = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.AUDIODESCRIPTION_CHOICES),
        verbose_name=translate_lazy("Équipement(s) audiodescription"),
        default=list,
        null=True,
        blank=True,
    )

    # Équipements pour personnes sourdes ou malentendantes
    accueil_equipements_malentendants_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_equipements_malentendants_presence"),
        verbose_name=translate_lazy("Présence d'équipement(s) sourds/malentendants"),
    )

    # Équipements pour personnes sourdes ou malentendantes
    accueil_equipements_malentendants = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.EQUIPEMENT_MALENTENDANT_CHOICES),
        verbose_name=translate_lazy("Équipement(s) sourd/malentendant"),
        default=list,
        null=True,
        blank=True,
    )

    # Cheminement de plain pied entre l’entrée et l’accueil
    accueil_cheminement_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Cheminement de plain pied"),
    )
    # Présence de marches entre l’entrée et l’accueil – nombre entre 0 et >10
    accueil_cheminement_nombre_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Nombre de marches"),
    )
    # Sens des marches de l'escalier
    accueil_cheminement_sens_marches = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Sens de circulation de l'escalier"),
        choices=schema.ESCALIER_SENS,
    )
    # Repérage des marches ou de l’escalier
    accueil_cheminement_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_cheminement_reperage_marches"),
        verbose_name=translate_lazy("Repérage des marches ou de l’escalier"),
    )
    # Main courante
    accueil_cheminement_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name=translate_lazy("Main courante"),
    )
    # Rampe – aucune / fixe / amovible / inconnu
    accueil_cheminement_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=schema.RAMPE_CHOICES,
        verbose_name=translate_lazy("Rampe"),
    )
    # Ascenseur / élévateur
    accueil_cheminement_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_cheminement_ascenseur"),
        verbose_name=translate_lazy("Ascenseur/élévateur"),
    )

    # Rétrécissement du cheminement
    accueil_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_retrecissement"),
        verbose_name=translate_lazy("Rétrécissement du cheminement"),
    )

    # Champs spécifiques hébergement sur l'accessibilité des chambres
    accueil_chambre_nombre_accessibles = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Nombre de chambres accessibles"),
    )
    accueil_chambre_douche_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_douche_plain_pied"),
        verbose_name=translate_lazy("Douche plain pied"),
    )
    accueil_chambre_douche_siege = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_douche_siege"),
        verbose_name=translate_lazy("Siège de douche"),
    )
    accueil_chambre_douche_barre_appui = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_douche_siege"),
        verbose_name=translate_lazy("Barre d'appui dans la douche"),
    )
    accueil_chambre_sanitaires_barre_appui = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_sanitaires_barre_appui"),
        verbose_name=translate_lazy("Barre d'appui dans les sanitaires"),
    )
    accueil_chambre_sanitaires_espace_usage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_sanitaires_espace_usage"),
        verbose_name=translate_lazy("Espace d'usage dans les sanitaires"),
    )
    accueil_chambre_numero_visible = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_numero_visible"),
        verbose_name=translate_lazy("Numéro de chambre visible et en relief"),
    )
    accueil_chambre_equipement_alerte = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_equipement_alerte"),
        verbose_name=translate_lazy("Equipement d'alerte dans la chambre"),
    )
    accueil_chambre_accompagnement = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("accueil_chambre_accompagnement"),
        verbose_name=translate_lazy("Accompagnement personnalisé pour présenter la chambre"),
    )

    ##############
    # Sanitaires #
    ##############
    sanitaires_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("sanitaires_presence"),
        verbose_name=translate_lazy("Sanitaires"),
    )

    sanitaires_adaptes = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.get_field_choices("sanitaires_adaptes"),
        verbose_name=translate_lazy("Nombre de sanitaires adaptés"),
    )

    ##########
    # labels #
    ##########
    labels = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.LABEL_CHOICES),
        verbose_name=translate_lazy("Marques ou labels"),
        default=list,
        null=True,
        blank=True,
    )
    labels_familles_handicap = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.HANDICAP_CHOICES),
        verbose_name=translate_lazy("Famille(s) de handicap concernées(s)"),
        default=list,
        null=True,
        blank=True,
    )
    labels_autre = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Autre label"),
    )

    #####################
    # Commentaire libre #
    #####################
    commentaire = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name=translate_lazy("Commentaire libre"),
    )

    ##########################
    # Registre               #
    ##########################
    registre_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=translate_lazy("URL du registre"),
    )

    ##########################
    # Conformité             #
    ##########################
    conformite = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=translate_lazy("Conformité"),
        choices=schema.get_field_choices("conformite"),
    )

    completion_rate = models.PositiveIntegerField(default=0, verbose_name=translate_lazy("Taux de complétion"))

    # Datetimes
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=translate_lazy("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=translate_lazy("Dernière modification"))

    def __str__(self):
        if self.erp:
            return translate(f'Accessibilité de l\'établissement "{self.erp.nom}" ({self.erp.code_postal})')
        else:
            return translate("Caractéristiques d'accessibilité de cet ERP")

    def __eq__(self, other):
        for field_name in schema.FIELDS:
            if getattr(self, field_name, None) != getattr(other, field_name, None):
                # FIXME: be able to compare None to []
                return False
        return True

    # NOTE: a class overriding `__eq__` MUST also override `__hash__`
    def __hash__(self):
        return super().__hash__()

    def get_history(self, exclude_changes_from=None):
        return _get_history(self.get_versions(), exclude_changes_from=exclude_changes_from)

    def get_versions(self):
        # take the last n revisions
        qs = (
            Version.objects.get_for_object(self)
            .select_related("revision__user")
            .order_by("-revision__date_created")[: self.HISTORY_MAX_LATEST_ITEMS + 1]
        )
        return reversed(list(qs))

    def has_data(self):
        # count the number of filled fields to provide more validation
        for field_name in schema.get_a11y_fields():
            if hasattr(self, field_name):
                field_value = getattr(self, field_name)
                if field_value not in [None, "", []]:
                    return True
        return False

    @property
    def easy_or_no_slope(self):
        return self.cheminement_ext_pente_presence in (False, None) or (
            self.cheminement_ext_pente_degre_difficulte == schema.PENTE_LEGERE
        )

    @property
    def little_or_no_camber(self):
        return self.cheminement_ext_devers in (schema.DEVERS_AUCUN, schema.DEVERS_LEGER, None)

    @property
    def provide_stair_equipement(self):
        return self.cheminement_ext_ascenseur or self.cheminement_ext_rampe in (
            schema.RAMPE_AMOVIBLE,
            schema.RAMPE_FIXE,
        )

    @property
    def stable_ground(self):
        return self.cheminement_ext_terrain_stable in (True, None)

    @property
    def entrance_has_min_width(self):
        return self.entree_largeur_mini is None or self.entree_largeur_mini >= 80

    @property
    def entrance_has_ramp(self):
        return self.entree_marches_rampe in (schema.RAMPE_FIXE, schema.RAMPE_AMOVIBLE)

    def has_outside_path_and_no_other_data(self):
        attrs = [
            f.name
            for f in Accessibilite._meta.get_fields()
            if f.name.startswith("cheminement_ext_") and f.name != "cheminement_ext_presence"
        ]
        return self.cheminement_ext_presence and all([getattr(self, attr) is None for attr in attrs])

    def has_camber(self):
        return self.cheminement_ext_devers and self.cheminement_ext_devers != schema.DEVERS_AUCUN

    def has_ramp_exterior_path(self):
        return self.cheminement_ext_rampe and self.cheminement_ext_rampe != schema.RAMPE_AUCUNE

    def has_ramp_entry(self):
        return self.entree_marches_rampe and self.entree_marches_rampe != schema.RAMPE_AUCUNE

    def has_ramp_reception(self):
        return self.accueil_cheminement_rampe and self.accueil_cheminement_rampe != schema.RAMPE_AUCUNE

    def _get_steps_direction_text(self, nb_steps, direction):
        if not nb_steps:
            nb_steps = 2  # Business rule: let assume it is plural
        if direction == schema.ESCALIER_MONTANT:
            return ngettext("montante", "montantes", nb_steps)
        if direction == schema.ESCALIER_DESCENDANT:
            return ngettext("descendante", "descendantes", nb_steps)

    def get_outside_steps_direction_text(self):
        return self._get_steps_direction_text(self.cheminement_ext_nombre_marches, self.cheminement_ext_sens_marches)

    def get_entry_steps_direction_text(self):
        return self._get_steps_direction_text(self.entree_marches, self.entree_marches_sens)

    def get_reception_steps_direction_text(self):
        return self._get_steps_direction_text(
            self.accueil_cheminement_nombre_marches, self.accueil_cheminement_sens_marches
        )

    def get_labels_display(self):
        if not self.labels:
            return
        label_to_text = {k: str(v) for k, v in schema.LABEL_CHOICES}
        return [(label, label_to_text.get(label)) for label in self.labels]

    def get_accueil_audiodescription_text(self):
        if not self.accueil_audiodescription:
            return
        equipment_to_text = {k: str(v) for k, v in schema.AUDIODESCRIPTION_CHOICES}
        return ",".join([equipment_to_text.get(equipment) for equipment in self.accueil_audiodescription])

    def get_accueil_equipements_malentendants_text(self):
        if not self.accueil_equipements_malentendants:
            return
        equipment_to_text = {k: str(v) for k, v in schema.EQUIPEMENT_MALENTENDANTS_TO_SHORT_TEXT}
        return [equipment_to_text.get(equipment).lower() for equipment in self.accueil_equipements_malentendants]

    def get_entree_dispositif_appel_type_text(self):
        if not self.entree_dispositif_appel_type:
            return
        equipment_to_text = {k: str(v) for k, v in schema.DISPOSITIFS_APPEL_CHOICES}
        return [equipment_to_text.get(equipment) for equipment in self.entree_dispositif_appel_type]

    def get_shower_text(self):
        text = ""
        needs_stopword = False
        if self.accueil_chambre_douche_plain_pied is True:
            text += schema.FIELDS["accueil_chambre_douche_plain_pied"]["help_text_ui_v2"]
        elif self.accueil_chambre_douche_plain_pied is False:
            text += schema.FIELDS["accueil_chambre_douche_plain_pied"]["help_text_ui_neg_v2"]
        else:
            text += translate_lazy("Douche")

        if self.accueil_chambre_douche_siege is True:
            needs_stopword = True
            text += " " + schema.FIELDS["accueil_chambre_douche_siege"]["help_text_ui_v2"].lower()
        elif self.accueil_chambre_douche_siege is False:
            text += " " + schema.FIELDS["accueil_chambre_douche_siege"]["help_text_ui_neg_v2"].lower()

        if self.accueil_chambre_douche_barre_appui is True:
            text += translate_lazy(" et ") if needs_stopword else " "
            text += schema.FIELDS["accueil_chambre_douche_barre_appui"]["help_text_ui_v2"].lower()
        elif self.accueil_chambre_douche_barre_appui is False:
            text += translate_lazy(" et ") if needs_stopword else " "
            text += schema.FIELDS["accueil_chambre_douche_barre_appui"]["help_text_ui_neg_v2"].lower()

        return text if text != translate_lazy("Douche") else None

    def get_labels_display_text(self):
        results = []
        for k, v in self.get_labels_display():
            if k == schema.LABEL_AUTRE:
                if self.labels_autre:
                    results.append((k, self.labels_autre))
            else:
                results.append((k, v))
        return results


class Departement(models.Model):
    code = models.CharField(max_length=3, null=False, blank=False)
    contour = models.MultiPolygonField(
        verbose_name=translate_lazy("Contour"),
        help_text=translate_lazy("Contour du département"),
        null=False,
    )

    def __str__(self):
        return translate(f"Département {self.code}")
