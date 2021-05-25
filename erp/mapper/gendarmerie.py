from datetime import datetime

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

    def process(self, records, activite: Activite) -> Erp:
        for record in records:
            print(record)
