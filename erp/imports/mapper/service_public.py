import logging
from datetime import datetime

from erp.models import Erp

logger = logging.getLogger(__name__)


class ServicePublicMapper:
    def __init__(self, record, source=None, activite=None, today=None):
        self.record = record
        self.today = today or datetime.today()
        self.activite = activite
        self.source = source

    def process(self):
        # NOTE: we search on both gendarmerie and service_public datasets as the gendarmerie import is taking
        # ownership on all the gendarmeries even on those initially coming from the service_public import
        try:
            erp = Erp.objects.find_by_source_id(
                [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE], self.record["ancien_code_pivot"], published=True
            ).get()
        except Erp.DoesNotExist:
            try:
                erp = Erp.objects.find_by_source_id(
                    [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE],
                    self.record["partenaire_identifiant"],
                    published=True,
                ).get()
            except Erp.DoesNotExist:
                return None, None

        erp.asp_id = self.record["id"]

        return erp, None
