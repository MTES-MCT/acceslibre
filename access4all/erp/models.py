import json
import requests

from django.db import models
from django.core.exceptions import ValidationError

from .domaines import DOMAINES_CHOICES


GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"


class Erp(models.Model):
    DOSSIER_ADAP = "adap"
    DOSSIER_ATTESTATION = "attestation"
    DOSSIER_ADAP_S = "adap_s"
    DOSSIER_AT_ADAP = "at_adap"
    DOSSIER_CHOICES = [
        (DOSSIER_ATTESTATION, "Attestation d’accessibilité pour un etablissement conforme"),
        (DOSSIER_ADAP, "Ad’AP: Agenda d’accessibilité programmé"),
        (DOSSIER_ADAP_S, "Ad’AP-S: Agenda d’accessibilité programmé simplifié"),
        (DOSSIER_AT_ADAP, "AT Ad’AP: Agenda d’axs prog associé à une autorisation de travaux"),
    ]
    CATEGORIE_CHOICES = [
        (1, "Catégorie 1"),
        (2, "Catégorie 2"),
        (3, "Catégorie 3"),
        (4, "Catégorie 4"),
        (5, "Catégorie 5"),
    ]
    NATURE_ERP = "ERP"
    NATURE_IOP = "IOP"
    NATURE_CHOICES = [
        ("erp", NATURE_ERP),
        ("iop", NATURE_IOP),
    ]

    gid = models.CharField(
        null=True, blank=True, max_length=255, help_text="Identifiant unique de l'enregistrement importé (si disponible)"
    )
    lat = models.FloatField(help_text="Latitude")
    lon = models.FloatField(help_text="Longitude")
    dossier = models.CharField(max_length=12, choices=DOSSIER_CHOICES, help_text="Type de dossier")
    id_adap = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Numéro d’autorisation pour suivi interne (num attestation, num at-adap…). Proposition de format pour attestations : « AC-X-Y » X = numéro département / Y = numéro de l’attestation",
    )
    demandeur = models.CharField(max_length=255, null=True, blank=True, help_text="Identité du demandeur")
    nom = models.CharField(max_length=255, help_text="Nom de l’établissement ou de l’enseigne")
    type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="type d’activité : liste SDIS - si plusieurs activités séparées par des virgules sans espaces (,).",
    )  # TODO: multiple choices
    nature = models.CharField(null=True, blank=True, max_length=255, choices=NATURE_CHOICES, help_text="ERP ou IOP")
    categorie = models.IntegerField(null=True, blank=True, choices=CATEGORIE_CHOICES, help_text="Catégorie si ERP (1 à 5)")
    date = models.DateField(null=True, blank=True, help_text="Date de validation de l’Ad’AP ou d’enregistrement de l’attestation")
    duree = models.IntegerField(null=True, blank=True, help_text="Durée d’Ad’AP en mois")
    siret = models.CharField(max_length=255, null=True, blank=True, help_text="Numéro SIRET")
    # adresse
    adresse = models.CharField(max_length=255, null=True, blank=True, help_text="Adresse complète")
    num = models.CharField(max_length=12, null=True, blank=True, help_text="Numéro dans la voie")
    cplt = models.CharField(max_length=255, null=True, blank=True, help_text="Complément de numéro (ex. BIS, TER)")
    voie = models.CharField(max_length=255, help_text="Voie")
    lieu_dit = models.CharField(max_length=255, null=True, blank=True, help_text="Lieu dit")
    cpost = models.CharField(max_length=10, help_text="Code postal")
    commune = models.CharField(max_length=255, help_text="Nom de la commune")
    code_insee = models.CharField(max_length=10, null=True, blank=True, help_text="Code INSEE")
    precision = models.FloatField(null=True, blank=True, help_text="Précision (géographique ?)")
    # derogation
    derog = models.BooleanField(null=True, blank=True, help_text="Dérogation existante sur ERP")
    objet_dero = models.TextField(null=True, blank=True, help_text="Point de non conformité concerné par la dérogation")
    qualite = models.CharField(null=True, blank=True, max_length=255, help_text="CHAMP À DOCUMENTER")
    domaine = models.CharField(null=True, blank=True, max_length=255, choices=DOMAINES_CHOICES, help_text="Domaine d’activités")

    def __str__(self):
        return f"ERP #{self.id} ({self.nom})"

    def clean(self):
        if self.adresse is None or self.adresse == "":
            self.adresse = " ".join(
                filter(lambda x: x is not None, [self.num, self.cplt, self.voie, self.lieu_dit, self.cpost, self.commune])
            ).strip()

    def geocode(self):
        # retrieve geolocoder data
        r = requests.get(GEOCODER_URL, {"q": self.adresse})
        if r.status_code != 200:
            return
        print(self)
        data = r.json()
        try:
            features = data["features"]
            if len(features) == 0:
                return
            feature = data["features"][0]
            print(json.dumps(feature, indent=2))
            # coordinates
            geometry = feature["geometry"]
            self.lat = geometry["coordinates"][1]
            self.lat = geometry["coordinates"][0]
            # address
            properties = feature["properties"]
            self.num = properties["housenumber"]
            # self.cplt = properties[""]
            self.voie = properties["street"]
            # self.lieu_dit = properties[""]
            self.cpost = properties["postcode"]
            self.commune = properties["city"]
            self.code_insee = properties["citycode"]
            print("all fine")
        except (KeyError, IndexError) as err:
            # print(json.dumps(data, indent=2))
            raise ValidationError({"adresse": f"Impossible de géocoder l'adresse: {err}."})
