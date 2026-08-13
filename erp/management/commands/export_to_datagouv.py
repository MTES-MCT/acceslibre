import logging
from datetime import datetime, timezone

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sentry_sdk import monitor

from erp.export.export import export_schema_to_csv, upload_to_datagouv
from erp.export.mappers import EtalabMapper
from erp.export.s3 import DATAGOUV_EXPORT_PREFIX, upload_csv_to_s3
from erp.models import Erp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Export and publish the data on datagouv"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", help="Display info")
        parser.add_argument("--skip-upload", action="store_true", help="Skip upload to datagouv and S3")
        parser.add_argument("--skip-s3", action="store_true", help="Skip upload to S3")
        parser.add_argument("--skip-datagouv", action="store_true", help="Skip upload to datagouv")

    def log(self, msg):
        if self.verbose:
            print(msg)

    @monitor(monitor_slug="export_to_datagouv")
    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        skip_upload = options.get("skip_upload", False)
        skip_s3 = options.get("skip_s3", False)
        skip_datagouv = options.get("skip_datagouv", False)

        csv_path = "acceslibre.csv"
        csv_path_with_url = "acceslibre-with-web-url.csv"
        self.log("Starting export")
        try:
            self.log("Récupération des ERPs")
            erps = Erp.objects.published().select_related("accessibilite", "activite")
            self.log(f"{erps.count()} ERP(s) trouvé(s)")
            export_schema_to_csv(csv_path_with_url, erps, EtalabMapper, logger=self.log)
            self.log(f"Local export successful: '{csv_path_with_url}'")

            df = pd.read_csv(csv_path_with_url)
            df.pop("web_url")
            df.pop("widget_code")
            df.to_csv(csv_path, index=False)

            self.log(f"Local export successful: '{csv_path}'")

            if skip_upload:
                self.log("Upload skipped.")
                return

            if not skip_datagouv:
                upload_to_datagouv(csv_path, resources_id=settings.DATAGOUV_RESOURCES_ID)
                upload_to_datagouv(csv_path_with_url, resources_id=settings.DATAGOUV_RESOURCES_WITH_URL_ID)
                self.log("Datasets uploaded to datagouv")

            if not skip_s3:
                self._upload_to_s3(csv_path)

        except RuntimeError as err:
            raise CommandError(f"Cannot publish the dataset: {err}")

    def _upload_to_s3(self, csv_path):
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        s3_key = f"{DATAGOUV_EXPORT_PREFIX}acceslibre_{today_str}.csv"
        upload_csv_to_s3(csv_path, s3_key)
        self.log(f"Uploaded to S3: {s3_key}")
