from erp.imports.mapper import SkippedRecord

ROOT_DATASETS_URL = "https://www.data.gouv.fr/fr/datasets/r"


class Importer:
    def __init__(self, id, fetcher, mapper, activite=None, today=None):
        self.id = id
        self.fetcher = fetcher
        self.mapper = mapper
        self.activite = activite
        self.today = today

    def process(self):
        records = self.fetcher.fetch(f"{ROOT_DATASETS_URL}/{self.id}")
        for record in records:
            try:
                (erp, unpublish_reason) = self.mapper(
                    record, self.activite, self.today
                ).process()
                if unpublish_reason:
                    print("MIS HORS LIGNE: " + unpublish_reason)
                    erp.published = False
                erp.save()
                print(".")
                # TODO: Handle logging
            except SkippedRecord as reason:
                print(f"ÉCARTÉ: : {reason}")
            # except UnpublishedRecord as err:
            #     erp = err.erp.save()
            #     print(f"MIS HORS LIGNE: {err} ({erp})")
            except RuntimeError as err:
                print(err)


# Importer(
#     "d0566522-604d-4af6-be44-a26eefa01756",
#     fetcher.JsonFetcher(hook=lambda x: x["features"]),
#     VaccinationMapper,
#     Activite.objects.get(slug="centre-de-vaccination"),
# ).process()

# Importer(
#     "061a5736-8fc2-4388-9e55-8cc31be87fa0",
#     fetcher.CsvFetcher(delimiter=";"),
#     GendarmerieMapper,
#     Activite.objects.get(slug="gendarmerie"),
# ).process()
