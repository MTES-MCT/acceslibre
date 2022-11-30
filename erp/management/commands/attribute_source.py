import csv
import os
import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from erp.models import Erp

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
    help = "Assigne la source c-conforme aux ERP existants en base"

    def handle_siret(self, siret):
        siret = clean(siret)
        if len(siret) == 14 and siret.isdigit():
            return siret

    def handle_5digits_code(self, cpost):
        cpost = clean(cpost).strip()
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def process_row(self, row, **kwargs):
        nom = clean(row["nom"])
        siret = self.handle_siret(row["siret"])
        code_insee = self.handle_5digits_code(row["code_insee"])
        code_postal = self.handle_5digits_code(row["cpost"])
        commune = clean_commune(row["commune"])
        gid = clean(row["gid"])

        # lookup
        try:
            erp = Erp.objects.get(
                nom=nom,
                commune=commune,
                code_postal=code_postal,
                code_insee=code_insee,
                siret=siret,
                # last cconforme import we know today (2020-05-27)
                created_at__lte=datetime(2020, 2, 28),
            )
            erp.source = "cconforme"
            erp.source_id = row["gid"]
            erp.save()
            print(f"{gid}: {nom} ({code_postal} {commune})")
            return None
        except Erp.MultipleObjectsReturned:
            return None
        except Erp.DoesNotExist:
            return None

    def get_csv_path(self):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(
            os.path.dirname(here),
            "data",
            "source.csv",
        )

    def handle(self, *args, **options):
        csv_path = self.get_csv_path()
        self.stdout.write(f"Importation des ERP depuis {csv_path}")

        with open(csv_path, "r") as file:
            reader = csv.DictReader(file)
            try:
                for row in reader:
                    self.process_row(row)
            except csv.Error as err:
                sys.exit(f"file {csv_path}, line {reader.line_num}: {err}")
        print("Mises à jour effectuées.")
