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
        def _search_by_old_code(old_code):
            return Erp.objects.find_by_source_id(
                [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE], old_code, published=True
            ).first()

        def _search_by_partner_id(partner_id):
            return Erp.objects.find_by_source_id(
                [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE],
                partner_id,
                published=True,
            ).first()

        def _search_by_name_address(name, address):
            if not self.record.get("adresse"):
                return
            postal_code = self.record["adresse"][0]["code_postal"]
            commune = self.record["adresse"][0]["nom_commune"]
            return (
                Erp.objects.search_what(name)
                .filter(code_postal=postal_code, commune__iexact=commune, published=True)
                .first()
            )

        erp = (
            _search_by_old_code(self.record["ancien_code_pivot"])
            or _search_by_partner_id(self.record["partenaire_identifiant"])
            or _search_by_name_address(self.record["nom"], self.record["adresse"])
        )

        if not erp:
            return None, None

        erp.asp_id = self.record["id"]

        return erp, None
