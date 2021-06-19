import logging

from django.conf import settings
from django.core.management.base import BaseCommand

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

    def log(self, msg):
        if self.verbose:
            print(msg)

    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        csv_path = "acceslibre.csv"
        self.log("Starting export")
        try:
            erps = Erp.objects.published().having_a11y_data()
            export_schema_to_csv(csv_path, erps, EtalabMapper)
            self.log("Local export successful: 'acceslibre.csv'")
            res = upload_to_datagouv(csv_path)
            if res:
                ping_mattermost(len(erps))
                self.log("Dataset uploaded")
        except RuntimeError as err:
            ping_mattermost(error=str(err))
            logger.error(f"Impossible de publier le dataset: {err}")


def ping_mattermost(count=0, error=None):
    status = error if error else "Aucune erreur rencontrée :thumbsup:"
    url = f"{settings.DATAGOUV_DOMAIN}/fr/datasets/acceslibre/"
    mattermost.send(
        "Export vers datagouv",
        attachements=[
            {
                "pretext": status,
                "text": f"- ERPs exportés: **{count}**\n[Lien vers le dataset]({url})",
            }
        ],
        tags=[__name__],
    )
