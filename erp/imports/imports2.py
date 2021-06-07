from erp.imports import fetcher
from erp.imports.mapper.vaccination import VaccinationMapper
from erp.imports.mapper.gendarmerie import GendarmerieMapper
from erp.models import Activite

ROOT_DATASETS_URL = "https://www.data.gouv.fr/fr/datasets/r"


class Importer:
    def __init__(self, id, fetcher, mapper, activite=None):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper
        self.activite = activite

    def process(self):
        records = self.fetcher.fetch(f"{ROOT_DATASETS_URL}/{self.id}")
        for record in records:
            try:
                (erp, discard_reason) = self.mapper(record, self.activite).process()
                # TODO: handle discarded
                if discard_reason:
                    erp.published = False
                erp.save()
                print(".")
                # TODO: Handle logging
            except RuntimeError as err:
                print(err)


Importer(
    "d0566522-604d-4af6-be44-a26eefa01756",
    fetcher.JsonFetcher(hook=lambda x: x["features"]),
    VaccinationMapper,
    Activite.objects.get(slug="centre-de-vaccination"),
).process()

Importer(
    "061a5736-8fc2-4388-9e55-8cc31be87fa0",
    fetcher.CsvFetcher(delimiter=";"),
    GendarmerieMapper,
    Activite.objects.get(slug="gendarmerie"),
).process()
