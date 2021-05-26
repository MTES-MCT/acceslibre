import logging

from django.conf import settings

from core import mailer
from erp.import_datasets.fetcher_strategy import CsvFetcher
from erp.import_datasets.import_datasets import ImportDatasets
from erp.management.commands.import_gendarmeries import fatal
from erp.mapper.vaccination import RecordMapper

logger = logging.getLogger(__name__)


def outputPrintStrategy(text, end="\n", flush=False):
    print(text, end=end, flush=flush)


def outputVoidStrategy(text, end="\n", flush=False):
    pass


class ImportGendarmerie:
    def job(self, dataset_url=None, verbose=False):
        try:
            fetcher = CsvFetcher(delimiter=";")
            mapper = RecordMapper(fetcher=fetcher, dataset_url=dataset_url)
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
