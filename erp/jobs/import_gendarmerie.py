# Imports vaccination centers from open data: https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/

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
            ImportDatasets(mapper=mapper).job(verbose=verbose)
            # ImportDatasets(mapper=mapper, is_scheduler=True).job()
        except RuntimeError as err:
            fatal(err)

    def _send_report(self):
        mailer.mail_admins(
            f"[{settings.SITE_NAME}] Rapport d'importation des centres de vaccination",
            "mail/import_vaccination_notification.txt",
            {
                "errors": self.errors,
                "imported": self.imported,
                "skipped": self.skipped,
                "SITE_NAME": settings.SITE_NAME,
                "SITE_ROOT_URL": settings.SITE_ROOT_URL,
            },
        )
