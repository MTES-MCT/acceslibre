import json

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from . import managers
from . import schema
from . import sirene
from .departements import DEPARTEMENTS

FULLTEXT_CONFIG = "french_unaccent"


class Activite(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    objects = managers.ActiviteQuerySet.as_manager()

    nom = models.CharField(max_length=255, unique=True, help_text="Nom de l'activité")
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text="Identifiant d'URL (slug)",
    )
    mots_cles = ArrayField(
        models.CharField(max_length=40, blank=True),
        verbose_name="Mots-clés",
        default=list,
        null=True,
        blank=True,
        help_text="Liste de mots-clés apparentés à cette activité",
    )
    icon = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        verbose_name="Icône",
        help_text=mark_safe(
            "Chemin de l'icône "
            '<a href="http://www.sjjb.co.uk/mapicons/contactsheet" target="_blank">SSJB</a> '
            "(ex. <code>sport_motorracing</code>)"
        ),
    )

    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return self.nom


def generate_commune_slug(instance):
    return f"{instance.departement}-{instance.nom}"


class Commune(models.Model):
    class Meta:
        ordering = ("nom",)

    objects = managers.CommuneQuerySet.as_manager()

    nom = models.CharField(max_length=255, help_text="Nom")
    slug = AutoSlugField(
        unique=True,
        populate_from=generate_commune_slug,
        unique_with=["departement", "nom"],
        help_text="Identifiant d'URL (slug)",
    )
    departement = models.CharField(
        max_length=3,
        verbose_name="Département",
        help_text="Codé sur deux ou trois caractères.",
    )
    code_insee = models.CharField(
        max_length=5, verbose_name="Code INSEE", help_text="Code INSEE de la commune",
    )
    superficie = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Superficie",
        help_text="Exprimée en hectares (ha)",
    )
    population = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Population",
        help_text="Nombre d'habitants estimé",
    )
    geom = models.PointField(
        verbose_name="Localisation",
        help_text="Coordonnées géographique du centre de la commune",
    )
    code_postaux = ArrayField(
        models.CharField(max_length=5),
        verbose_name="Codes postaux",
        default=list,
        help_text="Liste des codes postaux de cette commune",
    )

    def __str__(self):
        return f"{self.nom} ({self.departement})"

    def get_absolute_url(self):
        return reverse("commune", kwargs=dict(commune=self.slug))

    def departement_nom(self):
        nom = DEPARTEMENTS.get(self.departement, {}).get("nom")
        return f"{nom} ({self.departement})"

    def get_zoom(self):
        if not self.superficie or self.superficie > 8000:
            return 12
        elif self.superficie > 6000:
            return 13
        elif self.superficie > 1500:
            return 14
        else:
            return 15

    def toTemplateJson(self):
        return json.dumps(
            {
                "nom": self.nom,
                "slug": self.slug,
                "center": [self.geom.coords[1], self.geom.coords[0]],
                "zoom": self.get_zoom(),
            }
        )


class Label(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Label d'accessibilité"
        verbose_name_plural = "Labels d'accessibilité"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    nom = models.CharField(max_length=255, unique=True, help_text="Nom du label")
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text="Identifiant d'URL (slug)",
    )
    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return self.nom


class Vote(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["value"]),
            models.Index(fields=["erp", "value"]),
            models.Index(fields=["erp", "user", "value"]),
        ]
        unique_together = [["erp", "user"]]

    erp = models.ForeignKey(
        "Erp", verbose_name="Établissement", on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur", on_delete=models.CASCADE,
    )
    value = models.SmallIntegerField(
        verbose_name="Valeur", choices=[(-1, "-1"), (1, "+1")], default=1,
    )
    comment = models.TextField(
        max_length=5000, null=True, blank=True, verbose_name="Commentaire",
    )
    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return f"Vote {self.value} de {self.user.username} pour {self.erp.nom}"


class Erp(models.Model):
    SOURCE_ADMIN = "admin"
    SOURCE_API = "api"
    SOURCE_PUBLIC = "public"
    SOURCE_CCONFORME = "cconforme"
    SOURCE_CHOICES = (
        (SOURCE_ADMIN, "Back-office"),
        (SOURCE_API, "API"),
        (SOURCE_PUBLIC, "Application publique"),
        (SOURCE_CCONFORME, "cconforme"),
    )
    USER_ROLE_ADMIN = "admin"
    USER_ROLE_GESTIONNAIRE = "gestionnaire"
    USER_ROLE_PUBLIC = "public"
    USER_ROLE_SYSTEM = "system"
    USER_ROLES = (
        (USER_ROLE_ADMIN, "Administration"),
        (USER_ROLE_GESTIONNAIRE, "Gestionnaire"),
        (USER_ROLE_PUBLIC, "Utilisateur public"),
        (USER_ROLE_SYSTEM, "Système"),
    )

    class Meta:
        ordering = ("nom",)
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"
        indexes = [
            models.Index(fields=["source", "source_id"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["commune"]),
            models.Index(fields=["commune", "activite_id"]),
            models.Index(fields=["user_type"]),
            GinIndex(name="nom_trgm", fields=["nom"], opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["search_vector"]),
        ]

    objects = managers.ErpQuerySet.as_manager()

    source = models.CharField(
        max_length=100,
        null=True,
        verbose_name="Source",
        default=SOURCE_PUBLIC,
        choices=SOURCE_CHOICES,
        help_text="Nom de la source de données dont est issu cet ERP",
    )
    source_id = models.CharField(
        max_length=255,
        null=True,
        verbose_name="Source ID",
        help_text="Identifiant de l'ERP dans la source initiale de données",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name="Contributeur",
        on_delete=models.SET_NULL,
    )
    user_type = models.CharField(
        max_length=50,
        choices=USER_ROLES,
        verbose_name="Profil de contributeur",
        default=USER_ROLE_SYSTEM,
    )

    commune_ext = models.ForeignKey(
        Commune,
        null=True,
        blank=True,
        verbose_name="Commune (relation)",
        help_text="La commune de cet établissement",
        on_delete=models.SET_NULL,
    )
    nom = models.CharField(
        max_length=255, help_text="Nom de l'établissement ou de l'enseigne"
    )
    slug = AutoSlugField(
        default="",
        unique=True,
        populate_from="nom",
        help_text="Identifiant d'URL (slug)",
    )
    activite = models.ForeignKey(
        Activite,
        null=True,
        blank=True,
        verbose_name="Activité",
        help_text="Domaine d'activité de l'ERP. Attention, la recherche se fait sur les lettres accentuées",
        on_delete=models.SET_NULL,
    )
    published = models.BooleanField(
        default=True,
        verbose_name="Publié",
        help_text="Statut de publication de cet ERP: si la case est décochée, l'ERP ne sera pas listé publiquement",
    )
    geom = models.PointField(
        null=True,
        blank=True,
        verbose_name="Localisation",
        help_text="Géolocalisation (carte rafraîchie une fois l'enregistrement sauvegardé)",
    )
    siret = models.CharField(
        max_length=14,
        null=True,
        blank=True,
        verbose_name="SIRET",
        help_text="Numéro SIRET si l'ERP est une entreprise",
    )
    # contact
    telephone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de l'ERP",
    )
    site_internet = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Adresse du site internet de l'ERP",
    )
    contact_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Courriel",
        help_text="Adresse email permettant de contacter l'ERP",
    )
    # adresse
    numero = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Numéro",
        help_text="Numéro dans la voie, incluant le complément (BIS, TER, etc.)",
    )
    voie = models.CharField(max_length=255, null=True, blank=True, help_text="Voie")
    lieu_dit = models.CharField(
        max_length=255, null=True, blank=True, help_text="Lieu dit"
    )
    code_postal = models.CharField(max_length=5, help_text="Code postal")
    commune = models.CharField(max_length=255, help_text="Nom de la commune")
    code_insee = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Code INSEE",
        help_text="Code INSEE de la commune",
    )
    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )
    # search vector
    search_vector = SearchVectorField("Search vector", null=True)

    def __str__(self):
        return f"ERP #{self.id} ({self.nom}, {self.commune})"

    def get_activite_icon(self):
        default = "amenity_public_building"
        if self.activite and self.activite.icon:
            return self.activite.icon
        return default

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

    def get_absolute_url(self):
        if self.commune_ext:
            commune_slug = self.commune_ext.slug
        else:
            commune_slug = slugify(f"{self.departement}-{self.commune}")
        if self.activite is None:
            return reverse(
                "commune_erp", kwargs=dict(commune=commune_slug, erp_slug=self.slug),
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

    def has_accessibilite(self):
        return hasattr(self, "accessibilite") and self.accessibilite is not None

    @property
    def adresse(self):
        pieces = filter(
            lambda x: x is not None,
            [
                self.numero,
                self.voie,
                self.lieu_dit,
                self.code_postal,
                self.commune_ext.nom if self.commune_ext else self.commune,
            ],
        )
        return " ".join(pieces).strip().replace("  ", " ")

    @property
    def short_adresse(self):
        pieces = filter(
            lambda x: x is not None, [self.numero, self.voie, self.lieu_dit,],
        )
        return " ".join(pieces).strip().replace("  ", " ")

    @property
    def departement(self):
        return self.code_postal[:2]

    def clean(self):
        # Code postal
        if len(self.code_postal) != 5:
            raise ValidationError(
                {"code_postal": "Le code postal doit faire 5 caractères"}
            )

        # Voie OU lieu-dit sont requis
        if self.voie is None and self.lieu_dit is None:
            error = "Veuillez entrer une voie ou un lieu-dit"
            raise ValidationError({"voie": error, "lieu_dit": error})

        # Commune
        matches = Commune.objects.filter(
            nom__unaccent__iexact=self.commune,
            code_postaux__contains=[self.code_postal],
        )
        if len(matches) == 0:
            matches = Commune.objects.filter(code_insee=self.code_insee)
        if len(matches) == 0:
            raise ValidationError(
                {
                    "commune": f"Commune {self.commune} (code postal : {self.code_postal}) introuvable. "
                    "Merci de faire attention aux accents."
                }
            )
        else:
            self.commune_ext = matches[0]

        # SIRET
        if self.siret is not None:
            siret = sirene.validate_siret(self.siret)
            if siret is None:
                raise ValidationError({"siret": "Ce numéro SIRET est invalide."})
            self.siret = siret

    def vote(self, user, action, comment=None):
        votes = Vote.objects.filter(erp=self, user=user)
        if votes.count() > 0:
            vote = votes.first()
        else:
            vote = Vote(erp=self, user=user)
        vote.value = 1 if action == "UP" else -1
        vote.comment = comment if action == "DOWN" else None
        vote.save()
        return vote

    def save(self, *args, **kwargs):
        search_vector = SearchVector(
            Value(self.commune, output_field=models.TextField()),
            weight="A",
            config=FULLTEXT_CONFIG,
        )
        search_vector = search_vector + SearchVector(
            Value(self.code_postal, output_field=models.TextField()),
            weight="A",
            config=FULLTEXT_CONFIG,
        )
        if self.commune_ext:
            for code_postal in self.commune_ext.code_postaux:
                search_vector = search_vector + SearchVector(
                    Value(code_postal, output_field=models.TextField()),
                    weight="C",
                    config=FULLTEXT_CONFIG,
                )
        search_vector = search_vector + SearchVector(
            Value(self.nom, output_field=models.TextField()),
            weight="B",
            config=FULLTEXT_CONFIG,
        )
        search_vector = search_vector + SearchVector(
            Value(self.voie, output_field=models.TextField()),
            weight="B",
            config=FULLTEXT_CONFIG,
        )
        search_vector = search_vector + SearchVector(
            Value(self.lieu_dit, output_field=models.TextField()),
            weight="C",
            config=FULLTEXT_CONFIG,
        )
        if self.activite is not None:
            search_vector = search_vector + SearchVector(
                Value(self.activite.nom, output_field=models.TextField(),),
                weight="B",
                config=FULLTEXT_CONFIG,
            )
            if self.activite.mots_cles is not None:
                search_vector = search_vector + SearchVector(
                    Value(
                        " ".join(self.activite.mots_cles),
                        output_field=models.TextField(),
                    ),
                    weight="C",
                    config=FULLTEXT_CONFIG,
                )

        self.search_vector = search_vector
        super().save(*args, **kwargs)


class Accessibilite(models.Model):
    class Meta:
        verbose_name = "Accessibilité"
        verbose_name_plural = "Accessibilité"

    erp = models.OneToOneField(
        Erp,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Établissement",
        help_text="ERP",
    )

    ###################################
    # Transports en commun            #
    ###################################
    # Station de transport en commun
    transport_station_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Desserte par transports en commun",
    )
    transport_information = models.TextField(
        max_length=1000, null=True, blank=True, verbose_name="Informations transports",
    )

    ###################################
    # Stationnement                   #
    ###################################
    # Stationnement dans l'ERP
    stationnement_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnement dans l'ERP",
    )
    stationnement_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnements PMR dans l'ERP",
    )

    # Stationnement à proximité
    stationnement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnement à proximité de l'ERP",
    )
    stationnement_ext_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnements PMR à proximité de l'ERP",
    )

    ###################################
    # Espace et Cheminement extérieur #
    ###################################
    cheminement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Espace extérieur",
    )

    # Cheminement de plain-pied – oui / non / inconnu
    cheminement_ext_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Cheminement de plain-pied",
    )
    # Terrain meuble ou accidenté
    cheminement_ext_terrain_accidente = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Terrain meuble ou accidenté",
    )
    # Nombre de marches – nombre entre 0 et >10
    cheminement_ext_nombre_marches = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nombre de marches",
    )
    # Repérage des marches ou de l’escalier – oui / non / inconnu / sans objet
    cheminement_ext_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Repérage des marches ou de l’escalier",
    )
    # Main courante - oui / non / inconnu / sans objet
    cheminement_ext_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
    )
    # Rampe – oui / non / inconnu / sans objet
    cheminement_ext_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=schema.RAMPE_CHOICES,
        verbose_name="Rampe",
    )
    # Ascenseur / élévateur : oui / non / inconnu / sans objet
    cheminement_ext_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
    )

    # Pente - Aucune, légère, importante, inconnu
    cheminement_ext_pente = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=schema.PENTE_CHOICES,
        verbose_name="Pente",
    )

    # Dévers - Aucun, léger, important, inconnu
    cheminement_ext_devers = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Dévers",
        choices=schema.DEVERS_CHOICES,
    )

    # Bande de guidage – oui / non / inconnu
    cheminement_ext_bande_guidage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Bande de guidage",
    )

    # Rétrécissement du cheminement  – oui / non / inconnu
    cheminement_ext_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Rétrécissement du cheminement",
    )

    ##########
    # Entrée #
    ##########
    # Entrée facilement repérable  – oui / non / inconnu
    entree_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Entrée facilement repérable",
    )

    # Entrée vitrée
    entree_vitree = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée vitrée",
    )
    entree_vitree_vitrophanie = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Vitrophanie",
    )

    # Entrée de plain-pied
    entree_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée de plain-pied",
    )
    # Nombre de marches
    entree_marches = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Marches d'escalier",
    )
    # Repérage des marches ou de l'escalier
    entree_marches_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Repérage de l'escalier",
    )
    # Main courante
    entree_marches_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
    )
    # Rampe
    entree_marches_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Rampe",
        choices=schema.RAMPE_CHOICES,
    )
    # Système de guidage sonore  – oui / non / inconnu
    entree_balise_sonore = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Présence d'une balise sonore",
    )
    # Dispositif d’appel
    entree_dispositif_appel = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Dispositif d'appel",
    )
    entree_aide_humaine = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Aide humaine",
    )
    entree_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
    )

    # Largeur minimale
    entree_largeur_mini = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Largeur minimale",
    )

    # Entrée spécifique PMR
    entree_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée spécifique PMR",
    )

    # Informations sur l’entrée spécifique
    entree_pmr_informations = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Infos entrée spécifique PMR",
    )

    ###########
    # Accueil #
    ###########
    # Visibilité directe de la zone d'accueil depuis l’entrée
    accueil_visibilite = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Visibilité directe de la zone d'accueil depuis l'entrée",
    )

    # Personnel d’accueil
    accueil_personnels = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=schema.PERSONNELS_CHOICES,
        verbose_name="Personnel d'accueil",
    )

    # Équipements pour personnes sourdes ou malentendantes
    accueil_equipements_malentendants = ArrayField(
        models.CharField(
            max_length=255, blank=True, choices=schema.EQUIPEMENT_MALENTENDANT_CHOICES
        ),
        verbose_name="Équipement(s) sourd/malentendant",
        default=list,
        null=True,
        blank=True,
    )

    # Cheminement de plain pied entre l’entrée et l’accueil
    accueil_cheminement_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Cheminement de plain pied",
    )
    # Présence de marches entre l’entrée et l’accueil – nombre entre 0 et >10
    accueil_cheminement_nombre_marches = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nombre de marches",
    )
    # Repérage des marches ou de l’escalier
    accueil_cheminement_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Repérage des marches ou de l’escalier",
    )
    # Main courante
    accueil_cheminement_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
    )
    # Rampe – aucune / fixe / amovible / inconnu
    accueil_cheminement_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=schema.RAMPE_CHOICES,
        verbose_name="Rampe",
    )
    # Ascenseur / élévateur
    accueil_cheminement_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
    )

    # Rétrécissement du cheminement
    accueil_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Rétrécissement du cheminement",
    )

    # Prestations d'accueil adapté supplémentaires
    accueil_prestations = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Prestations d'accueil adapté supplémentaires",
    )

    ##############
    # Sanitaires #
    ##############
    sanitaires_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Sanitaires",
    )
    sanitaires_adaptes = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nombre de sanitaires adaptés",
    )

    ##########
    # labels #
    ##########
    labels = models.ManyToManyField(
        Label, blank=True, verbose_name="Marques ou labels",
    )
    labels_familles_handicap = ArrayField(
        models.CharField(max_length=255, blank=True, choices=schema.HANDICAP_CHOICES),
        verbose_name="Famille(s) de handicap concernées(s)",
        default=list,
        null=True,
        blank=True,
    )
    labels_autre = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Autre label",
    )

    #####################
    # Commentaire libre #
    #####################
    commentaire = models.TextField(
        max_length=1000, null=True, blank=True, verbose_name="Commentaire libre",
    )

    ##########################
    # Registre               #
    ##########################
    registre_url = models.URLField(
        max_length=255, null=True, blank=True, verbose_name="URL du registre",
    )

    ##########################
    # Conformité             #
    ##########################
    conformite = models.NullBooleanField(
        verbose_name="Conformité",
        null=True,
        blank=True,
        choices=schema.NULLABLE_BOOLEAN_CHOICES,
    )

    # Datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return "Caractéristiques d'accessibilité de cet ERP"

    def to_debug(self):
        cleaned = dict(
            [
                (k, v)
                for (k, v) in model_to_dict(self).copy().items()
                if v is not None and v != "" and v != []
            ]
        )
        return json.dumps(cleaned, indent=2)

    def has_cheminement_ext(self):
        fields = schema.get_section_fields(schema.SECTION_CHEMINEMENT_EXT)
        return any(getattr(f) is not None for f in fields)

    def has_data(self):
        # IDEA: count the number of filled fields to provide more validation
        for field_name in schema.get_a11y_fields():
            if hasattr(self, field_name):
                field_value = getattr(self, field_name)
                # This is the "simplest" way I've found for checking if a field is a
                # relation...
                if field_value.__class__.__name__ == "ManyRelatedManager":
                    if field_value.count() > 0:
                        return True
                elif field_value not in [None, "", []]:
                    return True
        return False
