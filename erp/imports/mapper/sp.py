import logging
from datetime import datetime

from erp.models import Erp

logger = logging.getLogger(__name__)


class SPMapper:
    def __init__(self, record, source=None, activite=None, today=None):
        self.record = record
        self.today = today if today is not None else datetime.today()
        self.activite = activite
        self.source = source

    def process(self):
        try:
            erp = Erp.objects.find_by_source_id(Erp.SOURCE_SERVICE_PUBLIC, self.record["ancien_code_pivot"]).get()
        except Erp.DoesNotExist:
            return None, None

        erp.asp_id = self.record["id"]

        return erp, None
