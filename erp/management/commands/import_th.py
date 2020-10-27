import csv
import os
import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import URLValidator
from django.db.models import Q

from erp.geocoder import geocode
from erp.models import Accessibilite, Activite, Commune, Erp, Label
from erp.provider import sirene

VALEURS_VIDES = ["-", "https://", "http://"]

ACTIVITES_MAP = {
    "Café, bar, brasserie": "Café, bar, brasserie",
    "Camping": "Camping caravaning",
    "Chambre d'hôtes": "Chambres d'hôtes",
    "Etablissement de loisir": "Centre de loisirs",
    "Hébergement collectif": "Hôtel",
    "Hébergement insolite": "Hôtel",
    "Hébergement": "Hôtel",
    "Hôtel": "Hôtel",
    "Information Touristique": "Information Touristique",
    "Lieu de visite": "Lieu de visite",
    "Loisir éducatif": "Sports et loisirs",
    "Loisir": "Centre de loisirs",
    "Meublé de tourisme": "Chambres d'hôtes",
    "Office de tourisme": "Office du tourisme",
    "Parc à thème": "Parc d’attraction",
    "Parc de loisir": "Centre de loisirs",
    "Piscine": "Piscine",
    "Résidence de tourisme": "Hôtel",
    "Restaurant": "Restaurant",
    "Restauration": "Restaurant",
    "Sport de nature": "Sports et loisirs",
    "Village de vacances": "Centre de vacances",
    "Visite d'entreprise": "Lieu de visite",
    "Visite guidée": "Lieu de visite",
}

FIELDS = {
    "NOM ETABLISSEMENT": "nom",
    "ADRESSE": "adresse",
    "SITE WEB ETABLISSEMENT": "site_internet",
    "TELEPHONE ETABLISSEMENT": "telephone",
    "COMMUNE": "commune",
    "CP": "code_postal",
    "CATEGORIE / FILIERE": "filiere",
    "ACTIVITE": "activite",
    "HANDICAPS": "handicaps",
    "SIRET": "siret",
}


def clean(string):
    if string in VALEURS_VIDES:
        return ""
    return (
        str(string)
        .replace("\n", " ")
        .replace("«", "")
        .replace("»", "")
        .replace("’", "'")
        .replace('"', "")
        .strip()
    )


class Command(BaseCommand):
    help = "Importe les données Tourisme & Handicap"

    def handle_siret(self, siret):
        siret = sirene.validate_siret(clean(siret))
        if siret:
            return siret

    def validate_site_internet(self, site_internet):
        if not site_internet:
            return
        validate = URLValidator()
        try:
            validate(clean(site_internet))
            return site_internet
        except ValidationError:
            return None

    def get_familles(self, source):
        if not source:
            return None
        return source.split(";")

    def map_row(self, row):
        mapped = {}
        for orig_key, target_key in FIELDS.items():
            mapped[target_key] = row.get(orig_key).strip()
        return mapped

    def find_activite(self, row):
        # Activité
        found_activite = None
        th_activites = row.get("activite", "").split(";")
        if len(th_activites) > 0:
            th_activite = th_activites[0].strip()
            if th_activite:
                found_activite = self.activites.get(th_activite)

        if found_activite:
            return found_activite

        # Fallback to filière
        filiere = row.get("filiere")
        if not filiere:
            return None
        filieres = filiere.split(";")
        if len(filieres) == 0:
            return
        return self.activites.get(filieres[0])

    def prepare_fields(self, row):
        row = self.map_row(row)
        siret = self.handle_siret(row["siret"])
        if not row or not siret or not row.get("adresse") or not row.get("code_postal"):
            return

        try:
            geo_info = geocode(row["adresse"], postcode=row["code_postal"])
        except RuntimeError as err:
            print(f"SKIP: {err}")
            return

        if not geo_info:
            return

        code_insee = geo_info.get("code_insee")

        activite = self.find_activite(row)

        commune_ext = (
            Commune.objects.filter(code_insee=code_insee).first()
            if code_insee
            else None
        )

        return {
            "source": Erp.SOURCE_TH,
            "source_id": f"th-{siret}",
            "nom": clean(row["nom"]).replace('"', ""),
            "siret": siret,
            "numero": geo_info.get("numero"),
            "voie": geo_info.get("voie"),
            "lieu_dit": geo_info.get("lieu_dit"),
            "code_postal": geo_info.get("code_postal"),
            "commune": geo_info.get("commune"),
            "code_insee": geo_info.get("code_insee"),
            "site_internet": self.validate_site_internet(row.get("site_internet")),
            "telephone": clean(row.get("telephone")) or None,
            "geom": geo_info.get("geom"),
            "commune_ext": commune_ext,
            "activite": activite,
        }

    def check_existing(self, fields):
        # check doublons
        try:
            Erp.objects.get(
                Q(siret=fields["siret"])
                | Q(nom=fields["nom"], voie=fields["voie"], commune=fields["commune"]),
            )
            print(f"EXIST {fields['nom']} {fields['voie']} {fields['commune']}")
            return True
        except Erp.MultipleObjectsReturned:
            # des doublons existent déjà malheureusement :(
            return True
        except Erp.DoesNotExist:
            return False

    def import_row(self, row, **kwargs):
        fields = self.prepare_fields(row)
        if not fields or self.check_existing(fields):
            return

        familles_handicaps = self.get_familles(row.get("handicaps"))

        # FIXME: migrate labels to be an array field (same one as for families)
        accessibilite = Accessibilite(labels_familles_handicap=familles_handicaps)
        accessibilite.labels.set([self.label])

        erp = Erp(accessibilite=accessibilite, **fields,)

        if erp.activite is not None:
            act = f"\n    {erp.activite.nom}"
        else:
            act = ""

        print(f"ADD {erp.nom}{act}\n    {erp.adresse}")
        return erp

    def handle(self, *args, **options):
        try:
            csv_path = os.path.join(settings.BASE_DIR, "data", "th-20200505.csv")
            self.stdout.write(f"Importation des ERP depuis {csv_path}")
            to_import = []

            self.label = Label.objects.get(nom="Tourisme & Handicap")
            self.activites = dict(
                [
                    (key, Activite.objects.get(nom=val))
                    for key, val in ACTIVITES_MAP.items()
                ]
            )

            with open(csv_path, "r") as file:
                reader = csv.DictReader(file)
                try:
                    for row in reader:
                        erp = self.import_row(row)
                        if erp is not None:
                            to_import.append(erp)
                except csv.Error as err:
                    sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
            if len(to_import) == 0:
                print("Rien à importer.")
                exit(0)
            else:
                print(f"Importing {len(to_import)} erps")
            # Erp.objects.bulk_create(to_import)
            print("Importation effectuée.")
        except KeyboardInterrupt:
            print("\nInterrompu.")
