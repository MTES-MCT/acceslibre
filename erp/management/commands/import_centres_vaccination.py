import sys

from django.core.management.base import BaseCommand

from erp.import_datasets.import_datasets import ImportDatasets
from erp.import_datasets.loader_strategy import JsonFetcher
from erp.jobs.import_centres_vaccination import ImportVaccinationsCenters
from erp.mapper.vaccination2 import RecordMapper


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    help = "Importe les centres de vaccination COVID"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-url",
            type=str,
            help="URL directe du jeu de données à importer",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )
        parser.add_argument(
            "--scheduler",
            action="store_true",
            help="Job: Execute et envoi un mail en fin d'opération",
        )

    def handle(self, *args, **options):  # noqa
        self.stdout.write("Importation des centres de vaccination")

        try:
            fetcher = JsonFetcher()
            mapper = RecordMapper(fetcher=fetcher)
            ImportDatasets(mapper=mapper).job(verbose=True)
            # ImportVaccinationsCenters(options["scheduler"]).job(
            #     dataset_url=options.get("dataset-url") or "",
            #     verbose=options["verbose"],
            # )
        except RuntimeError as err:
            fatal(err)
