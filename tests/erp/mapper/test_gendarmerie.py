import pytest

from erp.import_datasets.fetcher_strategy import StringFetcher
from erp.models import Activite, Erp
from tests.erp.mapper.fixtures import gendarmeries_valid
from erp.import_datasets.import_datasets import ImportDatasets
from erp.mapper.gendarmerie import RecordMapper


@pytest.fixture
def activite_cdv(db):
    return Activite.objects.get_or_create(nom="Gendarmerie")


@pytest.fixture
def import_dataset(gendarmeries_valid, db, activite_cdv):
    def _factory(dataset=gendarmeries_valid):
        fetcher = StringFetcher(dataset)
        mapper = RecordMapper(fetcher=fetcher, dataset_url="dummy")
        return ImportDatasets(mapper=mapper, is_scheduler=True)

    return _factory


def test_basic_stats(import_dataset):
    imported, skipped, errors = import_dataset().job()
    assert imported == 3, skipped == 0


def test_updated_data(import_dataset, gendarmeries_valid):
    import_dataset().job()

    gendarmeries_valid_updated = gendarmeries_valid.copy()
    gendarmeries_valid_updated[0]["code_commune_insee"] = "67000"
    imported, skipped, errors = import_dataset(gendarmeries_valid_updated).job()

    erp = Erp.objects.filter(
        source_id=gendarmeries_valid_updated[0]["identifiant_public_unite"]
    ).first()
    assert skipped == 0, len(errors) == 0
    assert erp is not None
    assert erp.code_insee == gendarmeries_valid_updated[0]["code_commune_insee"]
