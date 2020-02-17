import json
import requests

from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.urls import reverse

from . import managers


FULLTEXT_CONFIG = "french_unaccent"


class Activite(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Activité"
        verbose_name_plural = "Activités"

    objects = managers.ActiviteQuerySet.as_manager()

    nom = models.CharField(
        max_length=255, unique=True, help_text="Nom de l'activité"
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


class Label(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Label d'accessibilité"
        verbose_name_plural = "Labels d'accessibilité"

    nom = models.CharField(
        max_length=255, unique=True, help_text="Nom du label"
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


class EquipementMalentendant(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Équipement sourd/malentendant"
        verbose_name_plural = "Équipements sourd/malentendant"

    nom = models.CharField(
        max_length=255, unique=True, help_text="Nom de l'équipement"
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


class Erp(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"
        indexes = [
            GinIndex(
                name="nom_trgm", fields=["nom"], opclasses=["gin_trgm_ops"]
            ),
            GinIndex(fields=["search_vector"]),
        ]

    objects = managers.ErpQuerySet.as_manager()

    nom = models.CharField(
        max_length=255, help_text="Nom de l'établissement ou de l'enseigne"
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
        help_text="Statut de publication de cette fiche ERP: si la case est décochée, l'ERP ne sera pas listé publiquement.",
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
    # adresse
    numero = models.CharField(
        max_length=12,
        null=True,
        blank=True,
        verbose_name="Numéro",
        help_text="Numéro dans la voie, incluant le complément (BIS, TER, etc.)",
    )
    voie = models.CharField(
        max_length=255, null=True, blank=True, help_text="Voie"
    )
    lieu_dit = models.CharField(
        max_length=255, null=True, blank=True, help_text="Lieu dit"
    )
    code_postal = models.CharField(max_length=5, help_text="Code postal")
    commune = models.CharField(max_length=255, help_text="Nom de la commune")
    code_insee = models.CharField(
        max_length=5, null=True, blank=True, help_text="Code INSEE"
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
        return f"ERP #{self.id} ({self.nom})"

    def get_absolute_url(self):
        commune = f"{self.departement}-{self.commune.lower()}"
        # FIXME: either there shoudl be
        # - a page for erp with no activité
        # - activite should be a mandatory field
        if self.activite is None:
            return reverse("commune", kwargs=dict(commune=commune,),)
        else:
            return reverse(
                "commune_activite_erp",
                kwargs=dict(
                    commune=commune, activite=self.activite.pk, erp=self.pk,
                ),
            )

    @property
    def adresse(self):
        pieces = filter(
            lambda x: x is not None,
            [
                self.numero,
                self.voie,
                self.lieu_dit,
                self.code_postal,
                self.commune,
            ],
        )
        return " ".join(pieces).strip().replace("  ", " ")

    @property
    def departement(self):
        return self.code_postal[:2]

    def clean(self):
        # code postal
        if len(self.code_postal) != 5:
            raise ValidationError(
                {"code_postal": "Le code postal doit faire 5 caractères"}
            )
        # voie ou lieu-dit sont requis
        if self.voie is None and self.lieu_dit is None:
            error = "Veuillez entrer une voie ou un lieu-dit"
            raise ValidationError({"voie": error, "lieu_dit": error})

    def save(self, *args, **kwargs):
        self.search_vector = (
            SearchVector(
                Value(self.nom, output_field=models.TextField()),
                weight="A",
                config=FULLTEXT_CONFIG,
            )
            + SearchVector(
                Value(
                    self.activite and self.activite.nom or "",
                    output_field=models.TextField(),
                ),
                weight="B",
                config=FULLTEXT_CONFIG,
            )
            + SearchVector(
                Value(self.commune, output_field=models.TextField()),
                weight="C",
                config=FULLTEXT_CONFIG,
            )
            + SearchVector(
                Value(self.voie, output_field=models.TextField()),
                weight="D",
                config=FULLTEXT_CONFIG,
            )
            + SearchVector(
                Value(self.lieu_dit, output_field=models.TextField()),
                weight="D",
                config=FULLTEXT_CONFIG,
            )
        )
        super().save(*args, **kwargs)


class CriteresCommunsMixin(models.Model):
    class Meta:
        abstract = True

    RAMPE_AUCUNE = "aucune"
    RAMPE_FIXE = "fixe"
    RAMPE_AMOVIBLE = "amovible"
    RAMPE_AIDE_HUMAINE = "aide humaine"
    RAMPE_CHOICES = [
        (None, "Inconnu"),
        (RAMPE_AUCUNE, "Aucune"),
        (RAMPE_FIXE, "Fixe"),
        (RAMPE_AMOVIBLE, "Amovible"),
    ]

    reperage_vitres = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Répérage surfaces vitrées",
        help_text="Présence d'un repérage sur les surfaces vitrées",
    )
    guidage_sonore = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Système de guidage sonore",
        help_text="Présence d'un dispositif de guidage sonore",
    )
    largeur_mini = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Largeur minimale",
        help_text="Largeur minimale du passage ou rétrécissement, en centimètres",
    )
    rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=RAMPE_CHOICES,
        help_text="Présence et type de rampe",
    )
    aide_humaine = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence ou possibilité d'une aide humaine au déplacement",
    )
    escalier_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Marches d'escalier",
        help_text="Nombre de marches d'escalier. Indiquez 0 si pas d'escalier ou si présence d'un ascenseur/élévateur.",
    )
    escalier_reperage = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Repérage de l'escalier",
        help_text="Si marches contrastées, bande d'éveil ou nez de marche contrastés, indiquez “Oui”",
    )
    escalier_main_courante = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Main courante",
        help_text="Présence d'une main courante d'escalier",
    )
    ascenseur = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Ascenseur/élévateur",
        help_text="Présence d'un ascenseur ou d'un élévateur",
    )


class Accessibilite(CriteresCommunsMixin):
    class Meta:
        verbose_name = "Accessibilité"
        verbose_name_plural = "Accessibilité"

    PERSONNELS_AUCUN = "aucun"
    PERSONNELS_FORMES = "formés"
    PERSONNELS_NON_FORMES = "non-formés"
    PERSONNELS_CHOICES = [
        (None, "Inconnu"),
        (PERSONNELS_AUCUN, "Aucun personnel"),
        (PERSONNELS_FORMES, "Personnels sensibilisés et formés"),
        (PERSONNELS_NON_FORMES, "Personnels non-formés"),
    ]

    # erp
    erp = models.OneToOneField(
        Erp, on_delete=models.CASCADE, null=True, blank=True, help_text="ERP"
    )

    # stationnement dans l'ERP
    stationnement_presence = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Stationnement dans l'ERP",
        help_text="Présence de stationnements au sein de l'ERP",
    )
    stationnement_pmr = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Stationnements PMR dans l'ERP",
        help_text="Présence de stationnements PMR au sein de l'ERP",
    )

    # stationnement extérieur à proximité
    stationnement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Stationnement à proximité",
        help_text="Présence de stationnements à proximité (200m)",
    )
    stationnement_ext_pmr = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Stationnements PMR à proximité",
        help_text="Présence de stationnements PMR à proximité (200m)",
    )

    # entrées principale et PMR
    # note: le mixin CriteresCommunsMixin apporte des champs supplémentaires
    entree_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Plain-pied",
        help_text="L'entrée est-elle de plain-pied ?",
    )
    entree_reperage = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Repérage de l'entrée",
        help_text="Présence d'éléments de répérage de l'entrée",
    )
    entree_pmr = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Entrée spécifique PMR",
        help_text="Présence d'une entrée secondaire spécifique PMR",
    )
    entree_pmr_informations = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Infos entrée spécifique PMR",
        help_text="Précisions sur les modalités d'accès de l'entrée spécifique PMR",
    )
    entree_interphone = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Dispositif d'appel",
        help_text="Présence d'un dispositif d'appel (ex. interphone)",
    )

    # accueil
    accueil_visibilite = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Visibilité de la zone d'accueil",
        help_text="La zone d'accueil est-elle visible depuis l'entrée ?",
    )
    accueil_personnels = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=PERSONNELS_CHOICES,
        verbose_name="Personnel d'accueil",
        help_text="Présence et type de personnel d'accueil",
    )
    accueil_equipements_malentendants = models.ManyToManyField(
        EquipementMalentendant,
        blank=True,
        verbose_name="Équipements sourds/malentendants",
    )
    accueil_prestations = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Prestations d'accueil",
        help_text="Description libre des prestations adaptées",
    )

    # sanitaires
    sanitaires_presence = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Sanitaires",
        help_text="Présence de sanitaires dans l'établissement",
    )
    sanitaires_adaptes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de sanitaires adaptés",
        help_text="Nombre de sanitaires adaptés dans l'établissement",
    )

    # labels
    labels = models.ManyToManyField(
        Label, blank=True, help_text="Labels d'accessibilité obtenus par l'ERP",
    )

    # datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return f"Caractéristiques d'accessibilité de cet ERP"


class Cheminement(CriteresCommunsMixin):
    class Meta:
        unique_together = ("accessibilite", "type")
        verbose_name = "Cheminement"
        verbose_name_plural = "Cheminements"

    TYPE_INT_ENTREE_BATIMENT_ACCUEIL = "int_entree_batiment_vers_accueil"
    TYPE_EXT_STAT_VERS_ENTREE = "ext_stationnement_vers_entree"
    TYPE_EXT_ENTREE_PARCELLE_ENTREE_BATIMENT = (
        "ext_entree_parcelle_entree_vers_batiment"
    )
    TYPE_CHOICES = [
        (
            TYPE_INT_ENTREE_BATIMENT_ACCUEIL,
            "Cheminement intérieur de l'entrée du bâtiment jusqu'à l'accueil",
        ),
        (
            TYPE_EXT_STAT_VERS_ENTREE,
            "Cheminement extérieur de la place de stationnement de l'ERP à l'entrée",
        ),
        (
            TYPE_EXT_ENTREE_PARCELLE_ENTREE_BATIMENT,
            "Cheminement extérieur de l'entrée de la parcelle de terrain à l'entrée du bâtiment",
        ),
    ]

    DEVERS_AUCUN = "aucun"
    DEVERS_LEGER = "léger"
    DEVERS_IMPORTANT = "important"
    DEVERS_CHOICES = [
        (None, "Inconnu"),
        (DEVERS_AUCUN, "Aucun"),
        (DEVERS_LEGER, "Léger"),
        (DEVERS_IMPORTANT, "Important"),
    ]

    PENTE_AUCUNE = "aucune"
    PENTE_LEGERE = "légère"
    PENTE_IMPORTANTE = "importante"
    PENTE_CHOICES = [
        (None, "Inconnu"),
        (PENTE_AUCUNE, "Aucune"),
        (PENTE_LEGERE, "Légère"),
        (PENTE_IMPORTANTE, "Importante"),
    ]

    accessibilite = models.ForeignKey(Accessibilite, on_delete=models.CASCADE)

    type = models.CharField(
        max_length=100,
        default=TYPE_INT_ENTREE_BATIMENT_ACCUEIL,
        choices=TYPE_CHOICES,
        verbose_name="Type",
        help_text="Type de circulation",
    )

    # équipements
    # note: le mixin CriteresCommunsMixin apporte des champs supplémentaires
    bande_guidage = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Bande de guidage",
        help_text="Présence d'une bande de guidage",
    )
    # déclivité
    pente = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=PENTE_CHOICES,
        help_text="Présence et type de pente",
    )
    devers = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Dévers",
        choices=DEVERS_CHOICES,
        help_text="Inclinaison transversale du cheminement",
    )

    def __str__(self):
        try:
            return dict(self.TYPE_CHOICES)[self.type]
        except KeyError:
            return f"Type non supporté: {self.type}"
