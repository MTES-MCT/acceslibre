import csv
import os
import re

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from erp.models import Commune

# TODO: arg pour telecharger depuis https://sql.sh/ressources/sql-villes-france/villes_france.csv


class Command(BaseCommand):
    "Source de données: https://sql.sh/736-base-donnees-villes-francaises"

    help = "Importe les communes de France"

    def get_csv_path(self):
        here = os.path.abspath(
            os.path.join(os.path.abspath(__file__), "..", "..", "..")
        )
        return os.path.join(os.path.dirname(here), "data", "villes_france.csv",)

    def import_row(self, row):
        departement = row[1]
        assert len(departement) >= 2 and len(departement) <= 3, departement
        nom = row[5]
        assert len(nom) > 0, nom
        raw_code_postal = row[8]
        if "-" in raw_code_postal:
            code_postaux = raw_code_postal.split("-")
        else:
            code_postaux = [raw_code_postal]
        assert all(len(cp) == 5 for cp in code_postaux), code_postaux
        code_insee = row[10]
        assert len(code_insee) == 5, code_insee
        superficie = int(float(row[18]) * 1000)
        lon = float(row[19])
        lat = float(row[20])
        assert superficie != 0, (nom, superficie)
        return Commune(
            departement=departement,
            nom=nom,
            code_insee=code_insee,
            superficie=superficie,
            geom=Point(lon, lat, srid=4326),
            code_postaux=code_postaux,
        )

    def handle(self, *args, **options):
        csv_path = self.get_csv_path()
        self.stdout.write(f"Importation des communes depuis {csv_path}")
        to_import = []

        with open(csv_path, "r") as file:
            reader = csv.reader(file)
            try:
                for row in reader:
                    commune = self.import_row(row)
                    if commune is not None:
                        to_import.append(commune)
            except csv.Error as err:
                sys.exit(f"file {filename}, line {reader.line_num}: {err}")
        if len(to_import) == 0:
            print("Rien à importer.")
            exit(0)
        res = Commune.objects.bulk_create(to_import)
        print("Importation effectuée.")
