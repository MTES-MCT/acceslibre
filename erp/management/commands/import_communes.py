import csv
import os
import sys
import time

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from erp.geocoder import geocode_commune
from erp.models import Commune

# Le fichier source est téléchargeable à https://sql.sh/ressources/sql-villes-france/villes_france.csv
# Il faut l'enregistrer dans le répertoire `data` à la racine du dépôt.


class SkipImport(Exception):
    pass


class Command(BaseCommand):
    "Source de données: https://sql.sh/736-base-donnees-villes-francaises"

    help = "Importe les communes de France"

    def get_csv_path(self):
        here = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "..", ".."))
        return os.path.join(
            os.path.dirname(here),
            "data",
            "villes_france.csv",
        )

    def import_row(self, row):
        # TODO: check if exists
        code_insee = row[10]
        assert len(code_insee) == 5, code_insee
        if Commune.objects.filter(code_insee=code_insee).count() > 0:
            raise SkipImport("SKIP")
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
        superficie = int(float(row[18]) * 100)  # hectares
        lon = float(row[19])
        lat = float(row[20])
        assert superficie != 0, (nom, superficie)
        data = geocode_commune(code_insee)
        time.sleep(0.02)
        try:
            if data:
                departement = data["departement"]["code"]
                nom = data["nom"]
                superficie = data["surface"]  # hectares
                lon = data["centre"]["coordinates"][0]
                lat = data["centre"]["coordinates"][1]
                code_postaux = data["codesPostaux"]
            commune = Commune(
                departement=departement,
                nom=nom,
                code_insee=code_insee,
                superficie=superficie,  # hectares
                geom=Point(
                    lon,
                    lat,
                    srid=4326,
                ),
                code_postaux=code_postaux,
            )
        except KeyError as err:
            raise RuntimeError(f"{nom} ({departement}): Key error: {err}")
        except (AttributeError, IndexError, TypeError, ValueError) as err:
            raise RuntimeError(f"{nom} ({departement}): {err}")
        commune.save()

    def handle(self, *args, **options):
        self.errors = []
        csv_path = self.get_csv_path()
        self.stdout.write(f"Importation des communes depuis {csv_path}")

        with open(csv_path, "r") as file:
            reader = csv.reader(file)
            try:
                for row in reader:
                    try:
                        self.import_row(row)
                    except AssertionError as err:
                        self.errors.append(f"Validation error: line {reader.line_num}: {err}")
                        sys.stdout.write("E")
                        sys.stdout.flush()
                    except RuntimeError as err:
                        self.errors.append(f"Import error: line {reader.line_num}: {err}")
                        sys.stdout.write("E")
                        sys.stdout.flush()
                    except SkipImport:
                        sys.stdout.write("S")
                        sys.stdout.flush()
                    else:
                        sys.stdout.write(".")
                        sys.stdout.flush()
            except csv.Error as err:
                self.errors.append(f"CSV error: line {reader.line_num}: {err}")
                sys.stdout.write("E")
                sys.stdout.flush()

        if len(self.errors) != 0:
            print(f"{len(self.errors)} errors have been encountered:")
            for err in self.errors:
                print(f"- {err}")
            exit(1)
        print("Importation effectuée.")
