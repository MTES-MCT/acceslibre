from erp.imports import fetcher
from erp.imports.mapper.vaccination import VaccinationMapper
from erp.imports.mapper.gendarmerie import GendarmerieMapper


ROOT_DATASETS_API = "https://www.data.gouv.fr/api/1/datasets/"


class Importer:
    def __init__(self, id, fetcher, mapper):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper

    def process(self):
        # TODO: handle try/except stuff
        records = self.fetcher.fetch(f"{ROOT_DATASETS_API}/{self.id}")
        for record in records:
            (erp, discarded) = self.mapper(record).process()
            # TODO: handle discarded
            if discarded:
                erp.published = False
            erp.save()
            # Handle logging


Importer(
    "d0566522-604d-4af6-be44-a26eefa01756",
    fetcher.JsonFetcher(hook=lambda x: x["resouces"]),
    VaccinationMapper,
).process()

Importer(
    "061a5736-8fc2-4388-9e55-8cc31be87fa0",
    fetcher.CsvFetcher(delimiter=";"),
    GendarmerieMapper,
).process()
