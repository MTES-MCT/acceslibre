import pytest

from erp.import_datasets.import_datasets import ImportDatasets
from erp.mapper.gendarmerie import RecordMapper


@pytest.fixture
def fetcher():
    return


def test_basic_stats(fetcher):
    mapper = RecordMapper(fetcher=fetcher, dataset_url="dummy")
    imported, skipped, errors = ImportDatasets(mapper=mapper).job()
