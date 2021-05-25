import sys

from django.core.management.base import BaseCommand

from erp.import_datasets.import_datasets import ImportDatasets
from erp.import_datasets.fetcher_strategy import CsvFetcher
from erp.mapper.gendarmerie import RecordMapper


def fatal(msg):
    print(msg)
    sys.exit(1)


class Command(BaseCommand):
    help = "Importe les ERPs gendarmerie"

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
        self.stdout.write("Importation des ERPs gendarmerie")

        try:
            fetcher = CsvFetcher(delimiter=";")
            mapper = RecordMapper(
                fetcher=fetcher, dataset_url=options.get("dataset-url")
            )
            ImportDatasets(mapper=mapper).job(verbose=True)
            # ImportDatasets(mapper=mapper, is_scheduler=True).job()
        except RuntimeError as err:
            fatal(err)
