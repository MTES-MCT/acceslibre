import logging
import os
from datetime import datetime

from django.db import DatabaseError, DataError, transaction
from django.db.transaction import TransactionManagementError

from erp.imports import fetcher
from erp.imports.mapper import SkippedRecord
from erp.imports.mapper.gendarmerie import GendarmerieMapper
from erp.imports.mapper.generic import GenericMapper
from erp.imports.mapper.service_public import ServicePublicMapper
from erp.models import Accessibilite, Activite, ExternalSource

ROOT_DATASETS_URL = "https://www.data.gouv.fr/fr/datasets/r"

logger = logging.getLogger(__name__)


class Importer:
    def __init__(
        self,
        id,
        fetcher,
        mapper,
        activite=None,
        verbose=False,
        today=None,
        filepath=None,
        source=None,
    ):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper
        self.source = source
        self.activite = activite
        self.verbose = verbose
        self.today = today if today is not None else datetime.today()
        self.filepath = filepath

    def print_char(self, msg):
        if self.verbose:
            print(msg, end="", flush=True)

    def process(self):
        results = {
            "imported": [],
            "skipped": [],
            "unpublished": [],
            "errors": [],
            "activites_not_found": [],
        }
        here = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", ".."))
        resource_path = (
            os.path.join(os.path.dirname(here), "data", self.filepath)
            if self.filepath
            else f"{ROOT_DATASETS_URL}/{self.id}"
        )
        for record in self.fetcher.fetch(resource_path):
            erp = None
            try:
                mapper = self.mapper(record, activite=self.activite, today=self.today, source=self.source)
                (erp, sources, unpublish_reason) = mapper.process()
                if not erp:
                    self.print_char("X")
                    continue
                with transaction.atomic():
                    if unpublish_reason:
                        erp.published = False
                    erp.save()

                    if sources:
                        ExternalSource.objects.filter(source=mapper.source, erp_id=erp.id).delete()
                        for source in sources:
                            source.erp = erp
                            source.save()

                    # Attach an Accessibilite to newly created Erps
                    if not erp.has_accessibilite():
                        accessibilite = Accessibilite(erp=erp, entree_porte_presence=True)
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
                results["skipped"].append(f"{get_erp(erp)}: {skipped_reason}")
            except RuntimeError as err:
                self.print_char("E")
                results["errors"].append(f"{get_erp(erp)}: {str(err)}")
            except (TransactionManagementError, DataError, DatabaseError) as err:
                logger.error(f"Database error while importing dataset: {err}")
                self.print_char("E")
                results["errors"].append(f"{str(erp)}: {str(err)}")
            except Exception as e:
                if str(e) not in results["activites_not_found"]:
                    results["activites_not_found"].append(str(e))

        return results


def get_erp(erp):
    # Sometimes the ERP is not in base and get rejected, so "erp" is empty
    return str(erp) if erp else "ERP non répertorié"


def import_gendarmeries(verbose=False):
    return Importer(
        "061a5736-8fc2-4388-9e55-8cc31be87fa0",
        fetcher.CsvFetcher(delimiter=";"),
        GendarmerieMapper,
        Activite.objects.get(slug="gendarmerie"),
        verbose=verbose,
    ).process()


def import_generic(verbose=False):
    return Importer(
        "d0566522-604d-4af6-be44-a26eefa01756",
        fetcher.CsvFileFetcher(delimiter=";"),
        GenericMapper,
        verbose=verbose,
        filepath="import_generic.csv",
    ).process()


def import_service_public(verbose=False):
    return Importer(
        "73302880-e4df-4d4c-8676-1a61bb997f3d",
        fetcher.JsonCompressedFetcher(hook=lambda x: x["service"]),
        ServicePublicMapper,
        source=ExternalSource.SOURCE_SERVICE_PUBLIC,
        verbose=verbose,
    ).process()
