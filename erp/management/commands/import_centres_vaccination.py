import json
import sys

from django.core.management.base import BaseCommand

from erp.mapper.vaccination import RecordMapper
from erp.models import Activite


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    "Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"

    help = "Importe les établissements raxs de vaccination COVID"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les raisons d'écartement d'import de certains centres",
        )

    def handle(self, *args, **options):
        self.stdout.write("Importation des centres de vaccination")

        activite = Activite.objects.filter(slug="centre-de-vaccination").first()
        if not activite:
            fatal("L'activité Centre de vaccination n'existe pas.")

        errors = []
        imported = 0
        skipped = 0

        with open("data/centres-vaccination.json", "r") as json_file:
            json_data = json.load(json_file)
            if "features" not in json_data:
                fatal("Liste des centres manquante")
            for record in json_data["features"]:
                try:
                    erp = RecordMapper(record).process(activite)
                    if options["verbose"]:
                        print(f"- {erp.nom}\n  {erp.code_postal} {erp.commune_ext.nom}")
                    else:
                        sys.stdout.write(".")
                    imported += 1
                except RuntimeError as err:
                    if not options["verbose"]:
                        sys.stdout.write("S")
                    errors.append(err)
                    sys.stdout.flush()
                    skipped += 1

        if options["verbose"] and len(errors) > 0:
            print("Erreurs rencontrées :")
            for error in errors:
                print(f"- {error}")

        print("Opération effectuée:")
        print(f"- {imported} centres importés")
        print(f"- {skipped} écartés")
