# Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/
import logging
import sys

from django.conf import settings

from core import mailer
from erp.imports.fetcher import CsvFetcher, JsonFetcher
from erp.imports.importer import Importer
from erp.imports.mapper.vaccination import RecordMapper

logger = logging.getLogger(__name__)


def fatal(msg):
    print(msg)
    sys.exit(1)


class ImportVaccinationsCenters:
    def __init__(self, is_scheduler=False, mail_notification=False):
        self.mail_notification = mail_notification
        self.is_scheduler = is_scheduler

    def job(self, verbose=False):
        try:
            fetcher = JsonFetcher()
            mapper = RecordMapper(fetcher=fetcher)
            imported, skipped, errors = Importer(
                mapper=mapper, is_scheduler=self.is_scheduler
            ).job(verbose=verbose)

            if self.mail_notification:
                self._send_report(imported, skipped, errors)
        except RuntimeError as err:
            fatal(err)

    def _send_report(self, imported, skipped, errors):
        mailer.mail_admins(
            f"[{settings.SITE_NAME}] Rapport d'importation des centres de vaccination",
            "mail/import_notification.txt",
            {
                "errors": errors,
                "imported": imported,
                "skipped": skipped,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )
