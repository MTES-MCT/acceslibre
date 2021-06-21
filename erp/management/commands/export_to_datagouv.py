import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core import mattermost
from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Exporte et publie le jeu de données sur datagouv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les infos",
        )

        parser.add_argument(
            "--skip-upload",
            action="store_true",
            help="Export local uniquement",
        )

    def log(self, msg):
        if self.verbose:
            print(msg)

    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        skip_upload = options.get("skip-upload", False)

        csv_path = "acceslibre.csv"
        self.log("Starting export")
        try:
            erps = Erp.objects.published().having_a11y_data()
            export_schema_to_csv(csv_path, erps, EtalabMapper)
            self.log("Local export successful: 'acceslibre.csv'")
            if skip_upload:
                return
            res = upload_to_datagouv(csv_path)
            if res:
                ping_mattermost(len(erps))
                self.log("Dataset uploaded")
        except RuntimeError as err:
            raise CommandError(f"Impossible de publier le dataset: {err}")


def ping_mattermost(count):
    url = f"{settings.DATAGOUV_DOMAIN}/fr/datasets/acceslibre/"
    mattermost.send(
        "Export vers datagouv",
        attachements=[
            {
                "pretext": "Aucune erreur rencontrée :thumbsup:",
                "text": f"- ERPs exportés: **{count}**\n[Lien vers le dataset]({url})",
            }
        ],
        tags=[__name__],
    )
