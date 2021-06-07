from erp.imports import fetcher
from erp.imports.mapper.vaccination import VaccinationMapper
from erp.imports.mapper.gendarmerie import GendarmerieMapper


ROOT_DATASETS_URL = "https://www.data.gouv.fr/fr/datasets/r"


class Importer:
    def __init__(self, id, fetcher, mapper):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper

    def process(self):
        records = self.fetcher.fetch(f"{ROOT_DATASETS_URL}/{self.id}")
        for record in records:
            try:
                (erp, discarded) = self.mapper(record).process()
                # TODO: handle discarded
                if discarded:
                    erp.published = False
                erp.save()
                # TODO: Handle logging
            except RuntimeError as err:
                print(err)


Importer(
    "d0566522-604d-4af6-be44-a26eefa01756",
    fetcher.JsonFetcher(hook=lambda x: x["features"]),
    VaccinationMapper,
).process()

Importer(
    "061a5736-8fc2-4388-9e55-8cc31be87fa0",
    fetcher.CsvFetcher(delimiter=";"),
    GendarmerieMapper,
).process()
