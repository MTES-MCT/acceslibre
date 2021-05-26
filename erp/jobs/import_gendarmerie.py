import logging
import sys

from django.conf import settings

from core import mailer
from erp.import_datasets.fetcher_strategy import CsvFetcher
from erp.import_datasets.import_datasets import ImportDatasets
from erp.mapper.gendarmerie import RecordMapper

logger = logging.getLogger(__name__)


def fatal(msg):
    print(msg)
    sys.exit(1)


class ImportGendarmerie:
    def job(self, verbose=False):
        try:
            fetcher = CsvFetcher(delimiter=";")
            mapper = RecordMapper(fetcher=fetcher)
            imported, skipped, errors = ImportDatasets(mapper=mapper).job(
                verbose=verbose
            )
            self._send_report(imported, skipped, errors)
        except RuntimeError as err:
            fatal(err)

    def _send_report(self, imported, skipped, errors):
        mailer.mail_admins(
            f"[{settings.SITE_NAME}] Rapport d'importation des gendarmeries",
            "mail/import_vaccination_notification.txt",
            {
                "errors": errors,
                "imported": imported,
                "skipped": skipped,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )
