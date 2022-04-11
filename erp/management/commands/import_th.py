import csv
import os
import sys

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import URLValidator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils.text import slugify

from erp.geocoder import geocode
from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import sirene

VALEURS_VIDES = ["-", "https://", "http://"]

ACTIVITES_MAP = {
    "Café, bar, brasserie": "Café, bar, brasserie",
    "Camping": "Camping caravaning",
    "Chambre d'hôtes": "Pension, gîte, chambres d'hôtes",
    "Etablissement de loisir": "Centre de loisirs",
    "Hébergement collectif": "Hôtel",
    "Hébergement insolite": "Hôtel",
    "Hébergement": "Hôtel",
    "Hôtel": "Hôtel",
    "Information Touristique": "Information Touristique",
    "Information touristique": "Information Touristique",
    "Lieu de visite": "Lieu de visite",
    "Loisir éducatif": "Sports et loisirs",
    "Loisir": "Centre de loisirs",
    "Meublé de tourisme": "Pension, gîte, chambres d'hôtes",
    "Office de tourisme": "Office du tourisme",
    "Parc à thème": "Parc d’attraction",
    "Parc de loisir": "Centre de loisirs",
    "Piscine": "Piscine",
    "Résidence de tourisme": "Hôtel",
    "Restaurant": "Restaurant",
    "Restauration": "Restaurant",
    "Sport de nature": "Sports et loisirs",
    "Sortie nature": "Lieu de visite",
    "Village de vacances": "Centre de vacances",
    "Visite d'entreprise": "Lieu de visite",
    "Visite guidée": "Lieu de visite",
}

ACTIVITES_MAP_SEARCH = {
    "bibliotheque": "Bibliothèque médiathèque",
    "camping": "Camping caravaning",
    "chambre": "Pension, gîte, chambres d'hôtes",
    "chambres": "Pension, gîte, chambres d'hôtes",
    "gite": "Pension, gîte, chambres d'hôtes",
    "gites": "Pension, gîte, chambres d'hôtes",
    "hotel": "Hôtel",
    "mediatheque": "Bibliothèque médiathèque",
    "meuble": "Pension, gîte, chambres d'hôtes",
    "meubles": "Pension, gîte, chambres d'hôtes",
    "musee": "Musée",
    "musees": "Musée",
    "piscine": "Piscine",
    "restaurant": "Restaurant",
}

FIELDS = {
    "Nom Commercial": "nom",
    "Adresse 1": "adresse",
    "Site Web": "site_internet",
    "Téléphone": "telephone",
    "Ville": "commune",
    "Code Postal": "code_postal",
    "HANDICAPS": "handicaps",
}


class IncompleteError(Exception):
    pass


class GeoError(Exception):
    pass


class ExistError(Exception):
    pass


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
        handicaps = {
            "auditif": True if source.get("Auditif") == 1 else False,
            "mental": True if source.get("Mental") == 1 else False,
            "moteur": True if source.get("Moteur") == 1 else False,
            "visuel": True if source.get("Visuel") == 1 else False,
        }
        return [k for k, v in handicaps.items() if v is True]

    def map_row(self, row):
        mapped = {}
        for orig_key, target_key in FIELDS.items():
            mapped[target_key] = row.get(orig_key).strip()
        return mapped

    def compute_source_id(self, fields):
        parts = [fields["nom"], fields["voie"], fields["code_postal"]]
        parts = map(lambda x: slugify(x), parts)
        return "-".join(parts)

    def prepare_fields(self, row):
        row = self.map_row(row)
        if not row or not row.get("adresse") or not row.get("code_postal"):
            raise IncompleteError(f"Données manquantes: {row}")

        try:
            geo_info = geocode(row["adresse"], postcode=row["code_postal"])
        except RuntimeError as err:
            raise GeoError(
                f"Impossible de localiser cette adresse: {row.get('adresse')}: {err}"
            )

        if not geo_info:
            raise GeoError("Données de géolocalisation manquantes ou insatisfaisantes.")

        code_insee = geo_info.get("code_insee")

        commune_ext = (
            Commune.objects.filter(code_insee=code_insee).first()
            if code_insee
            else None
        )

        fields = {
            "published": True,
            "source": Erp.SOURCE_TH,
            "nom": clean(row["nom"]).replace('"', ""),
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
        }
        fields["source_id"] = self.compute_source_id(fields)
        return fields

    def check_existing(self, fields):
        # check doublons
        erpstr = f"{fields['nom']} {fields['voie']} {fields['commune']}"
        count = Erp.objects.filter(
            Q(source=Erp.SOURCE_TH, source_id=fields["source_id"])
            | Q(nom=fields["nom"], voie=fields["voie"], commune=fields["commune"])
        ).count()
        if count > 0:
            raise ExistError(f"Existe dans la base: {erpstr}")

    def import_row(self, row, **kwargs):
        familles_handicaps = self.get_familles(row)
        fields = self.prepare_fields(row)
        if not fields or self.check_existing(fields):
            return

        erp = Erp(**fields)
        erp.save()

        accessibilite = Accessibilite(
            erp=erp,
            labels=["th"],
            labels_familles_handicap=familles_handicaps,
            commentaire="Ces informations ont été importées.",
        )
        accessibilite.save()

        if erp.activite is not None:
            act = f"\n    {erp.activite.nom}"
        else:
            act = ""

        print(f"ADD {erp.nom}{act} - {erp.adresse}")
        return erp

    def handle(self, *args, **options):  # noqa
        report = {
            "imported": 0,
            "geo_errors": 0,
            "exists": 0,
            "incompletes": 0,
        }

        self.activites = dict(
            [(key, Activite.objects.get(nom=val)) for key, val in ACTIVITES_MAP.items()]
        )
        self.activites_search = dict(
            [
                (key, Activite.objects.get(nom=val))
                for key, val in ACTIVITES_MAP_SEARCH.items()
            ]
        )

        try:
            with transaction.atomic():
                csv_path = os.path.join(settings.BASE_DIR, "data", "th-20200505.csv")
                self.stdout.write(f"Importation des ERP depuis {csv_path}")

                with open(csv_path, "r") as file:
                    reader = csv.DictReader(file)
                    try:
                        for row in reader:
                            try:
                                self.import_row(row)
                                report["imported"] += 1
                            except GeoError:
                                report["geo_errors"] += 1
                            except ExistError:
                                report["exists"] += 1
                            except IncompleteError:
                                report["incompletes"] += 1
                    except csv.Error as err:
                        sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
                print(f"{report['imported']} erps importés.")
                print(f"{report['geo_errors']} erreurs de géolocalisation.")
                print(f"{report['exists']} erps déjà existants.")
                print(f"{report['incompletes']} erps incomplets.")
        except KeyboardInterrupt:
            print("\nInterrompu.")
        except IntegrityError as err:
            print(f"Erreurs d'intégrité rencontré : {err}")
        except Exception as err:
            print(f"Erreurs rencontrées, aucune donnée importée: {err}")
