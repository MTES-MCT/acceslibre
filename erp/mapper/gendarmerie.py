from datetime import datetime

from django.contrib.gis.geos import Point

from erp.import_datasets.base_mapper import BaseRecordMapper
from erp.import_datasets.loader_strategy import Fetcher
from erp.models import Activite, Erp


class RecordMapper(BaseRecordMapper):
    dataset_url = (
        "https://www.data.gouv.fr/fr/datasets/r/061a5736-8fc2-4388-9e55-8cc31be87fa0"
    )
    activite = "gendarmerie"

    def __init__(self, fetcher: Fetcher, dataset_url: str = dataset_url, today=None):
        self.today = today if today is not None else datetime.today()
        self.fetcher = fetcher

    def fetch_data(self):
        return self.fetcher.fetch(self.dataset_url)

    def process(self, record, activite: Activite) -> Erp:
        erp = Erp.objects.find_by_source_id(
            Erp.SOURCE_GENDARMERIE, record["identifiant_public_unite"]
        )
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_GENDARMERIE,
                source_id=record["identifiant_public_unite"],
                activite=activite,
                private_contact_email=record["identifiant_public_unite"],
                telephone=record["telephone"],
                code_insee=record["code_commune_insee"],
                code_postal=record["code_postal"],
                numero=record["code_postal"],
                voie=record["code_postal"],
                commune=record["code_postal"],
                geom=self._import_coordinates(record),
                site_internet=record["url"],
            )

        return erp

    def _import_coordinates(self, record):
        "Importe les coordonnées géographiques du centre de vaccination"
        try:
            (x, y) = record["geocodage_x_GPS"], record["geocodage_y_GPS"]
            return Point(x, y)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")
