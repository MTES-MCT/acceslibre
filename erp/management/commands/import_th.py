import csv
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from erp.geocoder import geocode
from erp.models import Activite, Commune, Erp
from erp.provider import sirene

VALEURS_VIDES = ["-", "https://", "http://"]

ACTIVITES_MAP = {
    "Hébergement": "Hôtel",
    "Information Touristique": "Information Touristique",
    "Loisir": "Centre de loisirs",
    "Restauration": "Restaurant",
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

    def map_row(self, row):
        mapped = {}
        for orig_key, target_key in FIELDS.items():
            mapped[target_key] = row.get(orig_key)
        return mapped

    def find_activite(self, row):
        # Activité
        found_activite = None
        th_activite = row.get("activite")
        if th_activite:
            pass

        # XXX find activite

        if found_activite:
            return found_activite

        # Fallback to filiere
        filiere = row.get("filiere")
        if not filiere:
            return None
        filieres = filiere.split(";")
        if len(filieres) == 0:
            return
        return self.activites.get(filieres[0])

    def prepare_fields(self, row):
        row = self.map_row(row)
        if not row:
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

        return {
            "nom": clean(row["nom"]).replace('"', ""),
            "siret": self.handle_siret(row["siret"]),
            "numero": geo_info.get("numero"),
            "voie": geo_info.get("voie"),
            "lieu_dit": geo_info.get("lieu_dit"),
            "code_postal": geo_info.get("code_postal"),
            "commune": geo_info.get("commune"),
            "code_insee": geo_info.get("code_insee"),
            "site_internet": clean(row.get("site_internet")) or None,
            "telephone": clean(row.get("telephone")) or None,
            "geom": geo_info.get("geom"),
            "commune_ext": Commune.objects.get(code_insee=code_insee)
            if code_insee
            else None,
            "activite": activite,
        }

    def check_existing(self, fields):
        # check doublons
        try:
            Erp.objects.get(
                nom=fields["nom"], voie=fields["voie"], commune=fields["commune"],
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

        print(fields)
        return

        erp = Erp(**fields)
        if erp.activite is not None:
            act = f"\n    {erp.activite.nom}"
        else:
            act = ""

        print(f"ADD {erp.nom}{act}\n    {erp.adresse}")
        return erp

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, "data", "th-20200505.csv")
        self.stdout.write(f"Importation des ERP depuis {csv_path}")
        to_import = []

        self.activites = dict(
            [(key, Activite.objects.get(nom=val)) for key, val in ACTIVITES_MAP.items()]
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
        # Erp.objects.bulk_create(to_import)
        print("Importation effectuée.")
