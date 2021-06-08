import logging

from datetime import datetime

from django.db import DataError, DatabaseError, transaction
from django.db.transaction import TransactionManagementError

from erp.imports.mapper import SkippedRecord
from erp.models import Accessibilite

ROOT_DATASETS_URL = "https://www.data.gouv.fr/fr/datasets/r"


logger = logging.getLogger(__name__)


class Importer:
    def __init__(self, id, fetcher, mapper, activite=None, verbose=False, today=None):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper
        self.activite = activite
        self.verbose = verbose
        self.today = today if today is not None else datetime.today()

    def print_char(self, msg):
        if self.verbose:
            print(msg, end="", flush=True)

    def process(self):
        results = {
            "imported": [],
            "skipped": [],
            "unpublished": [],
            "errors": [],
        }

        for record in self.fetcher.fetch(f"{ROOT_DATASETS_URL}/{self.id}"):
            try:
                mapper = self.mapper(record, self.activite, self.today)
                (erp, unpublish_reason) = mapper.process()
                if not erp:
                    self.log_char("X")
                    continue
                with transaction.atomic():
                    if unpublish_reason:
                        erp.published = False
                    erp.save()

                    # Attach an Accessibilite to newly created Erps
                    if not erp.has_accessibilite():
                        accessibilite = Accessibilite(erp=erp)
                        accessibilite.save()
                    else:
                        erp.accessibilite.save()

                    if unpublish_reason:
                        self.print_char("U")
                        results["unpublished"].append(f"{str(erp)}: {unpublish_reason}")
                    else:
                        self.print_char(".")
                        results["imported"].append(str(erp))
            except SkippedRecord as skipped_reason:
                self.print_char("S")
                results["skipped"].append(f"{str(erp)}: {skipped_reason}")
            except RuntimeError as err:
                self.print_char("E")
                results["errors"].append(f"{str(erp)}: {str(err)}")
            except (TransactionManagementError, DataError, DatabaseError) as err:
                logger.error(f"Database error while importing dataset: {err}")
                self.print_char("E")
                results["errors"].append(f"{str(erp)}: {str(err)}")

        return results
