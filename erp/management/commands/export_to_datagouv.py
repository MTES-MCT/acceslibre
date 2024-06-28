import logging

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sentry_sdk import monitor

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

    @monitor(monitor_slug="export_to_datagouv")
    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        skip_upload = options.get("skip_upload", False)

        csv_path = "acceslibre.csv"
        csv_path_with_url = "acceslibre-with-web-url.csv"
        self.log("Starting export")
        try:
            self.log("Récupération des ERPs")
            erps = Erp.objects.published()
            self.log(f"{erps.count()} ERP(s) trouvé(s)")
            export_schema_to_csv(csv_path_with_url, erps, EtalabMapper, logger=self.log)
            self.log(f"Local export successful: '{csv_path_with_url}'")

            df = pd.read_csv(csv_path_with_url)
            df.pop("web_url")
            df.to_csv(csv_path, index=False)

            self.log(f"Local export successful: '{csv_path}'")

            if skip_upload:
                self.log("Upload skipped.")
                return

            upload_to_datagouv(csv_path, resources_id=settings.DATAGOUV_RESOURCES_ID)
            upload_to_datagouv(csv_path_with_url, resources_id=settings.DATAGOUV_RESOURCES_WITH_URL_ID)
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
