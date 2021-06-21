import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Exporte vers datagouv"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les infos",
        )

        parser.add_argument(
            "--local",
            action="store_true",
            help="Export local uniquement",
        )

    def log(self, msg):
        if self.verbose:
            print(msg)

    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        local = options.get("local", False)

        csv_path = "acceslibre.csv"
        self.log("Starting export")
        try:
            erps = Erp.objects.published().having_a11y_data()
            export_schema_to_csv(csv_path, erps, EtalabMapper)
            self.log("Local export successful: 'acceslibre.csv'")
            if local:
                return
            res = upload_to_datagouv(csv_path)
            if res:
                ping_mattermost(len(erps))
                self.log("Dataset uploaded")
        except RuntimeError as err:
            ping_mattermost(error=str(err))
            raise RuntimeError(str(err))


def ping_mattermost(count=0, error=None):
    if not settings.MATTERMOST_HOOK or not settings.DATAGOUV_API_KEY:
        return
    status = error if error else "Aucune erreur rencontrée :thumbsup:"
    url = f"{settings.DATAGOUV_DOMAIN}/fr/datasets/acceslibre/"
    try:
        requests.post(
            settings.MATTERMOST_HOOK,
            json={
                "attachments": [
                    {
                        "pretext": "Export vers datagouv",
                        "text": f"- {status}\n- ERPs exportés: **{count}**\n[Lien vers le dataset]({url})",
                    }
                ],
            },
        )
    except requests.RequestException as err:
        logger.error(f"Couldn't send Mattermost notification: {err}")
