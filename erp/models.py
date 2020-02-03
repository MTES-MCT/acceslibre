import json
import requests

from django.contrib.gis.db import models


class Activite(models.Model):
    nom = models.CharField(
        max_length=255, unique=True, help_text="Nom de l'activité"
    )
    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


class Circulation(models.Model):
    RAMPE_FIXE = "fixe"
    RAMPE_AMOVIBLE = "amovible"
    RAMPE_CHOICES = [(RAMPE_FIXE, "Fixe"), (RAMPE_AMOVIBLE, "Amovible")]

    DEVERS_LEGER = "léger"
    DEVERS_IMPORTANT = "important"
    DEVERS_CHOICES = [(DEVERS_LEGER, "Léger"), (DEVERS_IMPORTANT, "Important")]

    PENTE_LEGERE = "légère"
    PENTE_IMPORTANTE = "importante"
    PENTE_CHOICES = [(PENTE_LEGERE, "Légère"), (PENTE_IMPORTANTE, "Importante")]

    # équipements
    reperage_vitres = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence d'un repérage sur les surfaces vitrées",
    )
    bande_guidage = models.BooleanField(
        null=True, blank=True, help_text="Présence d'une bande de guidage"
    )
    guidage_sonore = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence d'un dispositif de guidage sonore",
    )
    # largeur du passage
    largeur_mini = models.IntegerField(
        null=True, blank=True, help_text="Largeur minimale de la circulation"
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
        choices=DEVERS_CHOICES,
        help_text="Présence et type de dévers",
    )
    rampe = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=RAMPE_CHOICES,
        help_text="Présence et type d'une rampe",
    )
    # escalier
    escalier_marches = models.IntegerField(
        null=True,
        blank=True,
        help_text="Nombre de marches d'escalier, si applicable",
    )
    escalier_main_courante = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence d'une main courante d'escalier",
    )
    # ascenseur ou élévateur
    ascenseur = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence d'un ascenseur ou d'un élévateur",
    )


class Label(models.Model):
    nom = models.CharField(max_length=255)
    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


class Erp(models.Model):
    nom = models.CharField(
        max_length=255, help_text="Nom de l’établissement ou de l’enseigne"
    )
    activite = models.ForeignKey(
        Activite, null=True, blank=True, on_delete=models.SET_NULL
    )
    geom = models.PointField(null=True, blank=True)
    siret = models.CharField(
        max_length=255, null=True, blank=True, help_text="Numéro SIRET"
    )
    # adresse
    adresse = models.CharField(
        max_length=255, null=True, blank=True, help_text="Adresse complète"
    )
    numero = models.CharField(
        max_length=12, null=True, blank=True, help_text="Numéro dans la voie"
    )
    complement = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Complément de numéro (ex. BIS, TER)",
    )
    voie = models.CharField(max_length=255, help_text="Voie")
    lieu_dit = models.CharField(
        max_length=255, null=True, blank=True, help_text="Lieu dit"
    )
    code_postal = models.CharField(max_length=10, help_text="Code postal")
    commune = models.CharField(max_length=255, help_text="Nom de la commune")
    code_insee = models.CharField(
        max_length=10, null=True, blank=True, help_text="Code INSEE"
    )
    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ERP #{self.id} ({self.nom})"

    @property
    def adresse(self):
        pieces = filter(
            lambda x: x is not None,
            [
                self.numero,
                self.complement,
                self.voie,
                self.lieu_dit,
                self.code_postal,
                self.commune,
            ],
        )
        return " ".join(pieces).strip()


class Accessibilite(models.Model):
    PERSONNELS_FORMES = "formés"
    PERSONNELS_NON_FORMES = "non-formés"
    PERSONNELS_CHOICES = [
        (PERSONNELS_FORMES, "Personnels formés"),
        (PERSONNELS_NON_FORMES, "Personnels non-formés"),
    ]

    # erp
    # see https://docs.djangoproject.com/en/3.0/topics/db/examples/one_to_one/
    erp = models.OneToOneField(
        Erp, on_delete=models.CASCADE, null=True, blank=True, help_text="ERP"
    )

    # stationnement à proximité (simplification)
    presence = models.BooleanField(null=True, blank=True)
    reserve_pmr = models.BooleanField(null=True, blank=True)

    # cheminements
    cheminement_stationnement = models.ForeignKey(
        Circulation,
        related_name="accessibilite_cheminement_stationnement",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Cheminement depuis le stationnement de l'ERP",
    )
    cheminement_stationnement_ext = models.ForeignKey(
        Circulation,
        related_name="accessibilite_cheminement_stationnement_ext",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Cheminement depuis le stationnement extérieur à l'ERP",
    )
    cheminement_place_entree = models.ForeignKey(
        Circulation,
        related_name="accessibilite_cheminement_place_entree",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Cheminement du stationnement à l'entrée du bâtiment",
    )
    cheminement_parcelle_entree = models.ForeignKey(
        Circulation,
        related_name="accessibilite_cheminement_parcelle_entree",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Cheminement depuis l'entrée de la parcelle de terrain à l'entrée du bâtiment",
    )
    cheminement_entree_accueil = models.ForeignKey(
        Circulation,
        related_name="accessibilite_cheminement_entree_accueil",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Cheminement de l'entrée du bâtiment à l'accueil",
    )

    # entrées principale et secondaires
    entree_circulation = models.ForeignKey(
        Circulation,
        related_name="accessibilite_entree",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Caractéristiques d'accessibilité de l'entrée principale",
    )
    entree_signaletique = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence d'une signalétique matérialisant l'entrée",
    )
    entree_secondaire = models.BooleanField(
        null=True, blank=True, help_text="Présence d'une entrée secondaire"
    )
    entree_secondaire_informations = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Précisions sur les modalités d'accès de l'entrée secondaire",
    )

    # accueil
    accueil_personnels = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        choices=PERSONNELS_CHOICES,
        help_text="Présence et type de personnels d'accueil",
    )
    accueil_lsf = models.BooleanField(
        null=True, blank=True, help_text="Présence d'équipements LSF"
    )
    accueil_bim = models.BooleanField(
        null=True, blank=True, help_text="Présence d'équipements BIM"
    )
    accueil_prestations = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Description libre des prestations adaptées",
    )

    # sanitaires
    sanitaires_presence = models.BooleanField(
        null=True,
        blank=True,
        help_text="Présence de sanitaires dans l'établissement",
    )
    sanitaires_adaptes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Nombre de sanitaires adaptés dans l'établissement",
    )

    # labels
    labels = models.ManyToManyField(Label)

    # datetimes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Accessibilité #{self.id}"
