import sys

from django.core.management.base import BaseCommand
from erp.imports.mapper.vaccination import RecordMapper

from erp.imports.fetcher import JsonFetcher
from erp.imports.importer import Importer


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
            mapper = RecordMapper(
                fetcher=fetcher, dataset_url=options.get("dataset-url")
            )
            Importer(mapper=mapper, is_scheduler=options.get("scheduler")).job(
                verbose=options.get("verbose")
            )
        except RuntimeError as err:
            fatal(err)
