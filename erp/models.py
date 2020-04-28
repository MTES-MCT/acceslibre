import json
import requests

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.urls import reverse

from . import managers
from .schema import ACCESSIBILITE_SCHEMA


FULLTEXT_CONFIG = "french_unaccent"
UNKNOWN = "Inconnu"
UNKNOWN_OR_NA = "Inconnu ou sans objet"
NULLABLE_BOOLEAN_CHOICES = (
    (True, "Oui"),
    (False, "Non"),
    (None, UNKNOWN),
)
NULLABLE_OR_NA_BOOLEAN_CHOICES = (
    (True, "Oui"),
    (False, "Non"),
    (None, UNKNOWN_OR_NA),
)


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


class EquipementMalentendant(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Équipement sourd/malentendant"
        verbose_name_plural = "Équipements sourd/malentendant"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    nom = models.CharField(max_length=255, unique=True, help_text="Nom de l'équipement")
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


class Erp(models.Model):
    class Meta:
        ordering = ("nom",)
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["commune"]),
            models.Index(fields=["commune", "activite_id"]),
            GinIndex(name="nom_trgm", fields=["nom"], opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["search_vector"]),
        ]

    objects = managers.ErpQuerySet.as_manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name="Créateur",
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
        help_text="Statut de publication de cet ERP: si la case est décochée, l'ERP ne sera pas listé publiquement.",
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

    def get_absolute_url(self):
        commune = f"{self.departement}-{self.commune.lower()}"
        if self.activite is None:
            return reverse(
                "commune_erp", kwargs=dict(commune=commune, erp_slug=self.slug),
            )
        else:
            return reverse(
                "commune_activite_erp",
                kwargs=dict(
                    commune=commune,
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
            [self.numero, self.voie, self.lieu_dit, self.code_postal, self.commune,],
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
        # code postal
        if len(self.code_postal) != 5:
            raise ValidationError(
                {"code_postal": "Le code postal doit faire 5 caractères"}
            )
        # voie OU lieu-dit sont requis
        if self.voie is None and self.lieu_dit is None:
            error = "Veuillez entrer une voie ou un lieu-dit"
            raise ValidationError({"voie": error, "lieu_dit": error})

    def save(self, *args, **kwargs):
        search_vector = SearchVector(
            Value(self.commune, output_field=models.TextField()),
            weight="A",
            config=FULLTEXT_CONFIG,
        )
        search_vector = search_vector + SearchVector(
            Value(self.nom, output_field=models.TextField()),
            weight="A",
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

    PERSONNELS_AUCUN = "aucun"
    PERSONNELS_FORMES = "formés"
    PERSONNELS_NON_FORMES = "non-formés"
    PERSONNELS_CHOICES = [
        (PERSONNELS_AUCUN, "Aucun personnel"),
        (PERSONNELS_FORMES, "Personnels sensibilisés et formés"),
        (PERSONNELS_NON_FORMES, "Personnels non-formés"),
        (None, UNKNOWN),
    ]

    DEVERS_AUCUN = "aucun"
    DEVERS_LEGER = "léger"
    DEVERS_IMPORTANT = "important"
    DEVERS_CHOICES = [
        (DEVERS_AUCUN, "Aucun"),
        (DEVERS_LEGER, "Léger"),
        (DEVERS_IMPORTANT, "Important"),
        (None, UNKNOWN_OR_NA),
    ]

    PENTE_AUCUNE = "aucune"
    PENTE_LEGERE = "légère"
    PENTE_IMPORTANTE = "importante"
    PENTE_CHOICES = [
        (PENTE_AUCUNE, "Aucune"),
        (PENTE_LEGERE, "Légère"),
        (PENTE_IMPORTANTE, "Importante"),
        (None, UNKNOWN_OR_NA),
    ]

    RAMPE_AUCUNE = "aucune"
    RAMPE_FIXE = "fixe"
    RAMPE_AMOVIBLE = "amovible"
    RAMPE_AIDE_HUMAINE = "aide humaine"
    RAMPE_CHOICES = [
        (RAMPE_AUCUNE, "Aucune"),
        (RAMPE_FIXE, "Fixe"),
        (RAMPE_AMOVIBLE, "Amovible"),
        (None, UNKNOWN),
    ]

    HANDICAP_AUDITIF = "auditif"
    HANDICAP_MENTAL = "mental"
    HANDICAP_MOTEUR = "moteur"
    HANDICAP_VISUEL = "visuel"
    HANDICAP_CHOICES = [
        (HANDICAP_AUDITIF, "Auditif"),
        (HANDICAP_MENTAL, "Mental"),
        (HANDICAP_MOTEUR, "Moteur"),
        (HANDICAP_VISUEL, "Visuel"),
    ]

    erp = models.OneToOneField(
        Erp,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Établissement",
        help_text="ERP",
    )
    # Station de transport en commun
    transport_station_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Desserte par transports en commun",
        help_text="Présence d'une station de transport en commun à proximité (500 m)",
    )
    # Stationnement dans l'ERP
    stationnement_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnement dans l'ERP",
        help_text="Existe-t-il une ou plusieurs places de stationnement au sein de la parcelle de l'ERP ?",
    )
    stationnement_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnements PMR dans l'ERP",
        help_text="Existe-t-il une ou plusieurs places de stationnement adaptées ?",
    )

    # Stationnement à proximité
    stationnement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnement à proximité de l'ERP",
        help_text="Présence de stationnements à proximité de l'ERP (200m)",
    )
    stationnement_ext_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Stationnements PMR à proximité de l'ERP",
        help_text="Existe-t-il une ou plusieurs places de stationnement en voirie ou "
        "en parking à proximité de l'ERP (200m) ?",
    )

    ###################################
    # Espace et Cheminement extérieur #
    ###################################

    cheminement_ext_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Espace extérieur",
        help_text="L'établissement dispose-t-il d'un espace extérieur qui lui appartient ?",
    )

    # Cheminement de plain-pied – oui / non / inconnu
    cheminement_ext_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Cheminement de plain-pied",
        help_text="Le cheminement est-il de plain-pied ou existe-t-il une rupture de "
        "niveau entraînant la présence de marches ou d'un équipement type ascenseur ?",
    )
    # Nombre de marches – nombre entre 0 et >10
    cheminement_ext_nombre_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de marches",
        help_text="Indiquez 0 s’il n’y a ni marche ni escalier",
    )
    # Repérage des marches ou de l’escalier – oui / non / inconnu / sans objet
    cheminement_ext_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Repérage des marches ou de l’escalier",
        help_text="Nez de marche contrasté, bande d'éveil à la vigilance en haut "
        "de l'escalier, première et dernière contremarches de l'escalier contrastées",
    )
    # Main courante - oui / non / inconnu / sans objet
    cheminement_ext_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
        help_text="Présence d'une main courante d'escalier",
    )
    # Rampe – oui / non / inconnu / sans objet
    cheminement_ext_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=RAMPE_CHOICES,
        verbose_name="Rampe",
        help_text="Présence et type de rampe",
    )
    # Ascenseur / élévateur : oui / non / inconnu / sans objet
    cheminement_ext_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
        help_text="Présence d'un ascenseur ou d'un élévateur",
    )

    # Pente - Aucune, légère, importante, inconnu
    cheminement_ext_pente = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        choices=PENTE_CHOICES,
        verbose_name="Pente",
        help_text="Présence et type de pente",
    )

    # Dévers - Aucun, léger, important, inconnu
    cheminement_ext_devers = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Dévers",
        choices=DEVERS_CHOICES,
        help_text="Inclinaison transversale du cheminement",
    )

    # Bande de guidage – oui / non / inconnu
    cheminement_ext_bande_guidage = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Bande de guidage",
        help_text="Présence d'une bande de guidage au sol facilitant le déplacement "
        "d'une personne aveugle ou malvoyante",
    )

    # Système de guidage sonore  – oui / non / inconnu
    cheminement_ext_guidage_sonore = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Système de guidage sonore",
        help_text="Présence d'un système de guidage sonore aidant le déplacement "
        "d'une personne aveugle ou malvoyante",
    )

    # Rétrécissement du cheminement  – oui / non / inconnu
    cheminement_ext_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Rétrécissement du cheminement",
        help_text="Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) "
        "du chemin emprunté par le public pour atteindre l'entrée ?",
    )

    ##########
    # Entrée #
    ##########

    # Entrée facilement repérable  – oui / non / inconnu
    entree_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Entrée facilement repérable",
        help_text="Y a-t-il des éléments de repérage de l'entrée (numéro de rue à "
        "proximité, enseigne, etc)",
    )

    # Entrée vitrée
    entree_vitree = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée vitrée",
        help_text="La porte d'entrée est-elle vitrée ?",
    )
    entree_vitree_vitrophanie = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Vitrophanie",
        help_text="Si l'entrée est vitrée, présence d'éléments contrastés permettant "
        "de visualiser l'entrée ?",
    )

    # Entrée de plain-pied
    entree_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée de plain-pied",
        help_text="L'entrée est-elle de plain-pied ?",
    )
    # Nombre de marches
    entree_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Marches d'escalier",
        help_text="Nombre de marches d'escalier",
    )
    # Repérage des marches ou de l'escalier
    entree_marches_reperage = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Repérage de l'escalier",
        help_text="Nez de marche contrasté, bande d'éveil à la vigilance en haut "
        "de l'escalier, première et dernière contremarches de l'escalier contrastées",
    )
    # Main courante
    entree_marches_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
        help_text="Présence d'une main courante pour franchir les marches",
    )
    # Rampe
    entree_marches_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Rampe",
        choices=RAMPE_CHOICES,
        help_text="Présence et type de rampe",
    )
    # Dispositif d’appel
    entree_dispositif_appel = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Dispositif d'appel",
        help_text="Existe-t-il un dispositif comme une sonnette pour permettre à "
        "quelqu'un ayant besoin de la rampe de signaler sa présence ?",
    )
    entree_aide_humaine = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Aide humaine",
        help_text="Présence ou possibilité d'une aide humaine au déplacement",
    )
    entree_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
        help_text="Présence d'un ascenseur ou d'un élévateur",
    )

    # Largeur minimale
    entree_largeur_mini = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Largeur minimale",
        help_text="Si la largeur n’est pas précisément connue, indiquez une valeur "
        "minimum. Exemple : ma largeur se situe entre 90 et 100 cm ; indiquez 90.",
    )

    # Entrée spécifique PMR
    entree_pmr = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Entrée spécifique PMR",
        help_text="Présence d'une entrée secondaire spécifique PMR",
    )

    # Informations sur l’entrée spécifique
    entree_pmr_informations = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Infos entrée spécifique PMR",
        help_text="Précisions sur les modalités d'accès de l'entrée spécifique PMR",
    )

    ###########
    # Accueil #
    ###########

    # Visibilité directe de la zone d'accueil depuis l’entrée
    accueil_visibilite = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Visibilité directe de la zone d'accueil depuis l'entrée",
        help_text="La zone d'accueil (guichet d’accueil, caisse, secrétariat, etc) "
        "est-elle visible depuis l'entrée ?",
    )

    # Personnel d’accueil
    accueil_personnels = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=PERSONNELS_CHOICES,
        verbose_name="Personnel d'accueil",
        help_text="Présence et sensibilisation du personnel d'accueil",
    )

    # Équipements pour personnes sourdes ou malentendantes
    accueil_equipements_malentendants = models.ManyToManyField(
        EquipementMalentendant,
        blank=True,
        verbose_name="Équipements sourds/malentendants",
        help_text="L'accueil est-il équipé de produits ou prestations dédiés aux personnes "
        "sourdes ou malentendantes (boucle à induction magnétique, langue des signes "
        "françaises, solution de traduction à distance, etc)",
    )

    # Cheminement de plain pied entre l’entrée et l’accueil
    accueil_cheminement_plain_pied = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Cheminement de plain pied",
        help_text="Le cheminement entre l’entrée et l’accueil est-il de plain-pied ?",
    )
    # Présence de marches entre l’entrée et l’accueil – nombre entre 0 et >10
    accueil_cheminement_nombre_marches = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de marches",
        help_text="Indiquez 0 s’il n’y a ni marche ni escalier",
    )
    # Repérage des marches ou de l’escalier
    accueil_cheminement_reperage_marches = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Repérage des marches ou de l’escalier",
        help_text="Nez de marche contrasté, bande d'éveil à la vigilance en haut "
        "de l'escalier, première et dernière contremarches de l'escalier contrastées",
    )
    # Main courante
    accueil_cheminement_main_courante = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_OR_NA_BOOLEAN_CHOICES,
        verbose_name="Main courante",
        help_text="Présence d'une main courante d'escalier",
    )
    # Rampe – aucune / fixe / amovible / inconnu
    accueil_cheminement_rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=RAMPE_CHOICES,
        verbose_name="Rampe",
        help_text="Présence et type de rampe",
    )
    # Ascenseur / élévateur
    accueil_cheminement_ascenseur = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Ascenseur/élévateur",
        help_text="Présence d'un ascenseur ou d'un élévateur",
    )

    # Rétrécissement du cheminement
    accueil_retrecissement = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Rétrécissement du cheminement",
        help_text="Existe-t-il un ou plusieurs rétrécissements (inférieur à 80 cm) "
        "du chemin emprunté par le public pour atteindre la zone d’accueil ?",
    )

    # Prestations d'accueil adapté supplémentaires
    accueil_prestations = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Prestations d'accueil adapté supplémentaires",
        help_text="Veuillez indiquer ici les prestations spécifiques supplémentaires "
        "proposées par l'établissement",
    )

    ##############
    # Sanitaires #
    ##############

    sanitaires_presence = models.BooleanField(
        null=True,
        blank=True,
        choices=NULLABLE_BOOLEAN_CHOICES,
        verbose_name="Sanitaires",
        help_text="Présence de sanitaires dans l'établissement",
    )
    sanitaires_adaptes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de sanitaires adaptés",
        help_text="Nombre de sanitaires adaptés dans l'établissement",
    )

    ##########
    # labels #
    ##########

    labels = models.ManyToManyField(
        Label,
        blank=True,
        verbose_name="Labels d'accessibilité",
        help_text="Labels d'accessibilité obtenus par l'ERP",
    )
    labels_familles_handicap = ArrayField(
        models.CharField(max_length=255, blank=True, choices=HANDICAP_CHOICES),
        verbose_name="Famille(s) de handicap concernées(s)",
        default=list,
        null=True,
        blank=True,
        help_text="Liste des familles de handicaps couverts par l'obtention de ce label",
    )
    labels_autre = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Autre label",
        help_text="Si autre, précisez le nom du label",
    )

    #####################
    # Commentaire libre #
    #####################
    commentaire = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name="Commentaire libre",
        help_text="Indiquez tout autre information qui vous semble pertinente pour "
        "décrire l’accessibilité du bâtiment",
    )

    # Datetimes
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Dernière modification"
    )

    def __str__(self):
        return f"Caractéristiques d'accessibilité de cet ERP"

    def has_cheminement_ext(self):
        fields = ACCESSIBILITE_SCHEMA["cheminement_ext"]["fields"]
        return any(getattr(f) is not None for f in fields)
