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
        fetcher = StringFetcher(dataset, RecordMapper.fields)
        mapper = RecordMapper(fetcher=fetcher, dataset_url="dummy")
        return ImportDatasets(mapper=mapper, is_scheduler=True)

    yield _factory


def test_basic_stats(import_dataset, gendarmeries_valid):
    imported, skipped, errors = import_dataset().job()
    erp = Erp.objects.filter(
        source_id=gendarmeries_valid[0]["identifiant_public_unite"]
    ).first()
    assert erp is not None
    assert imported == 3, skipped == 0


def test_updated_data(import_dataset, gendarmeries_valid):
    import_dataset().job()

    gendarmeries_valid_updated = gendarmeries_valid.copy()
    gendarmeries_valid_updated[0]["code_commune_insee"] = "67000"
    imported, skipped, errors = import_dataset(gendarmeries_valid_updated).job()

    erp = Erp.objects.filter(
        source_id=gendarmeries_valid_updated[0]["identifiant_public_unite"]
    ).first()
    assert erp is not None
    assert erp.code_insee == gendarmeries_valid_updated[0]["code_commune_insee"]
    assert skipped == 0, len(errors) == 0


def test_invalid_data(import_dataset, gendarmeries_valid):
    gendarmeries_invalid = gendarmeries_valid.copy()
    gendarmeries_invalid[0]["code_commune_insee"] = "67000azdasqd"

    imported, skipped, errors = import_dataset(gendarmeries_invalid).job()
    assert len(errors) == 1, imported == 2


def test_fail_on_schema_change(import_dataset, gendarmeries_valid):
    gendarmeries_invalid = gendarmeries_valid.copy()
    gendarmeries_invalid[0]["code_insee"] = "test"
    del gendarmeries_invalid[0]["code_commune_insee"]

    imported, skipped, errors = import_dataset(gendarmeries_invalid).job()
    assert imported == 2, skipped == 1
