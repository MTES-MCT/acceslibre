import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


class Command(BaseCommand):
    help = "Exporte vers datagouv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Afficher les erreurs",
        )

    def log(self, msg):
        if self.verbose:
            print(msg)

    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        csv_path = "acceslibre.csv"
        with open(csv_path, "w", newline="") as csv_file:
            try:
                erps = Erp.objects.published().having_a11y_data()
                export_schema_to_csv(csv_file, erps, EtalabMapper)
                self.log("Local export successful: 'acceslibre.csv'")
                res = upload_to_datagouv(csv_path)
                if res:
                    ping_mattermost()
                self.log("Dataset updated")
            except Exception as err:
                if settings.DATAGOUV_API_KEY:
                    ping_mattermost(str(err))
                raise err


def ping_mattermost(error=None):
    if not settings.MATTERMOST_HOOK:
        return
    status = error if error else "Aucune erreur rencontrée"
    requests.post(
        settings.MATTERMOST_HOOK,
        json={
            "text": f"Export vers datagouv: {status}",
        },
    )
