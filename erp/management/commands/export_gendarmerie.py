import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from erp.export.export import export_schema_to_csv
from erp.export.mappers import PartooMapper
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Exporte le jeu de données en csv (A lancer en local)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les infos",
        )

    def log(self, msg):
        if self.verbose:
            print(msg)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise Exception("Script à lancer EN LOCAL uniquement")

        self.verbose = options.get("verbose", False)

        csv_path = "gendarmerie.csv"
        self.log("Starting export")
        try:
            erps = Erp.objects.published().having_a11y_data().filter(activite__slug="gendarmerie")
            export_schema_to_csv(csv_path, erps, PartooMapper)
            self.log("Local export successfull: '%s'" % csv_path)

        except RuntimeError as err:
            raise CommandError(f"Erreur lors de l'export du dataset: {err}")
