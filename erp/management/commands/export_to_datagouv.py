import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core import mattermost
from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper, EtalabMapperWithUrl
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
            self.log("Récupération des ERPs")
            erps = Erp.objects.published()
            self.log(f"{erps.count()} ERP(s) trouvé(s)")
            export_schema_to_csv(csv_path, erps, EtalabMapper, logger=self.log)
            self.log("Local export successful: 'acceslibre.csv'")
            export_schema_to_csv(
                "acceslibre-with-web-url.csv",
                erps,
                EtalabMapperWithUrl,
                logger=self.log,
            )
            self.log("Local export successful: 'acceslibre-with-web-url.csv'")

            if skip_upload:
                return
            upload_to_datagouv(csv_path)
            upload_to_datagouv(
                "acceslibre-with-web-url.csv",
                resources_id="93ae96a7-1db7-4cb4-a9f1-6d778370b640",
            )
            self.log("Datasets uploaded")

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
