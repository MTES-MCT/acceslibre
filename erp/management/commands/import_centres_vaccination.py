import sys

from django.core.management.base import BaseCommand
from erp.jobs import import_centres_vaccination


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
            help="Afficher les raisons d'écartement d'import de certains centres",
        )
        parser.add_argument(
            "--report",
            action="store_true",
            help="Envoi un mail en fin d'opération",
        )

    def handle(self, *args, **options):  # noqa
        self.stdout.write("Importation des centres de vaccination")

        try:
            import_centres_vaccination.job(
                dataset_url=options["dataset-url"],
                verbose=options["verbose"],
                report=options["report"],
            )
        except RuntimeError as err:
            fatal(err)
