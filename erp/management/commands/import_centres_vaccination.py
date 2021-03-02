import requests
import sys

from django.core.management.base import BaseCommand

from erp.mapper.vaccination import RecordMapper
from erp.models import Activite


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    "Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"

    help = "Importe les centres de vaccination COVID"
    api_url = "https://www.data.gouv.fr/api/1/datasets/lieux-de-vaccination-contre-la-covid-19/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-url",
            type=str,
            help="URL directe du jeu de données à importer",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les raisons d'écartement d'import de certains centres",
        )

    def get_json(self, url):
        try:
            return requests.get(url).json()
        except requests.exceptions.RequestException as err:
            raise RuntimeError(
                f"Erreur de récupération des données JSON: {url}:\n  {err}"
            )

    def retrieve_latest_dataset_url(self):
        try:
            json_data = self.get_json(self.api_url)
            json_resources = [
                resource
                for resource in json_data["resources"]
                if resource["format"] == "json"
            ]
            if len(json_resources) == 0:
                raise RuntimeError("Jeu de donnée JSON abenst.")
            return json_resources[0]["latest"]
        except (KeyError, IndexError, ValueError) as err:
            raise RuntimeError(
                f"Impossible de parser les données depuis {self.api_url}:\n{err}"
            )

    def retrieve_json_data(self, dataset_url):
        return self.get_json(dataset_url)

    def handle(self, *args, **options):  # noqa
        self.stdout.write("Importation des centres de vaccination")

        try:
            if "dataset-url" in options:
                json_data = self.retrieve_json_data(options["dataset-url"])
            else:
                latest_dataset_url = self.retrieve_latest_dataset_url()
                json_data = self.retrieve_json_data(latest_dataset_url)
        except RuntimeError as err:
            print(err)
            sys.exit(1)

        activite = Activite.objects.filter(slug="centre-de-vaccination").first()
        if not activite:
            fatal("L'activité Centre de vaccination n'existe pas.")

        errors = []
        imported = 0
        skipped = 0

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
