import csv
import os
import sys

from django.core.management.base import BaseCommand

from erp.models import Activite, Erp, Commune
from erp.provider.geocoder import geocode

VILLES_CIBLES = [r"^Lyon$", r"^Clichy$"]
VALEURS_VIDES = [
    "nr",
    "non renseigné",
    "non renseignée",
    "Non renseigné(e)",
    "#N/A",
]


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


def clean_commune(string):
    return clean("".join(i for i in string if not i.isdigit()))


class Command(BaseCommand):
    help = "Importe les données restaurant pour gamma"

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def import_row(self, row, **kwargs):
        fields = {}

        # nom
        fields["nom"] = clean(row["nom"])
        try:
            geo_info = geocode(row["adresse"], postcode=row["cp"])
        except Exception as e:
            print(f"Erreur géocodage : {e}")
            return None
        else:
            if not geo_info:
                print("Adresse introuvable")
                return None

        code_insee = geo_info.get("code_insee")

        commune_ext = (
            Commune.objects.filter(code_insee=code_insee).first()
            if code_insee
            else None
        )

        fields["source"] = "sap"
        fields["published"] = True
        fields["numero"] = geo_info.get("numero")
        fields["voie"] = geo_info.get("voie")
        fields["lieu_dit"] = geo_info.get("lieu_dit")
        fields["code_postal"] = geo_info.get("code_postal")
        fields["commune"] = geo_info.get("commune")
        fields["geom"] = geo_info.get("geom")
        fields["commune_ext"] = commune_ext

        # checks rest
        if any(
            [
                fields["nom"] == "",
                fields["code_postal"] == "",
                fields["commune"] == "",
                fields["voie"] == "" and fields["lieu_dit"] == "",
                fields["geom"] == "",
            ]
        ):
            return None

        # check doublons
        try:
            Erp.objects.get(
                nom=fields["nom"],
                voie=fields["voie"],
                commune=fields["commune"],
            )
            print(f"EXIST {fields['nom']} {fields['voie']} {fields['commune']}")
            return None
        except Erp.MultipleObjectsReturned:
            # des doublons existent déjà malheureusement :(
            return None
        except Erp.DoesNotExist:
            if fields["nom"] in [(erp.nom,) for erp in self.to_import]:
                print(f"Doublonner dans le fichier source")
                return None
        # activité
        fields["activite_id"] = Activite.objects.get(nom="Restaurant").id

        erp = Erp(**fields)
        act = f"\n    Restaurant"

        print(f"ADD {erp.nom}{act}\n    {erp.adresse}")
        return erp

    def get_csv_path(self):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(
            os.path.dirname(here),
            "data",
            "restaurant_gamma.csv",
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=f"Mode test",
        )

    def handle(self, *args, **options):
        self.dry_run = options.get("dry-run", False)
        csv_path = self.get_csv_path()
        self.stdout.write(f"Importation des ERP depuis {csv_path}")
        self.to_import = []

        with open(csv_path, "r") as file:
            reader = csv.DictReader(file)
            try:
                for row in reader:
                    erp = self.import_row(row)
                    if erp is not None:
                        self.to_import.append(erp)
            except csv.Error as err:
                sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
        if len(self.to_import) == 0:
            print("Rien à importer.")
            exit(0)
        else:
            print(f"{len(self.to_import)} ERP à importer")
            print(f"{self.to_import}")
        if not self.dry_run:
            Erp.objects.bulk_create(self.to_import)
            print("Importation effectuée.")
        else:
            print("Mode test actif. Aucune sauvegarde en bdd")
