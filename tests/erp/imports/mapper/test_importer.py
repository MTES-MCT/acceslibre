from datetime import datetime

import pytest
from django.db import DataError

from erp.imports.fetcher import JsonFetcher
from erp.imports.imports2 import Importer
from erp.imports.mapper.vaccination import VaccinationMapper
from erp.models import Activite, Erp
from tests.erp.imports.mapper.fixtures import FakeJsonFetcher

from tests.erp.imports.mapper.fixtures import neufchateau, sample_record_ok


@pytest.fixture
def activite_cdv(db):
    return Activite.objects.create(nom="Centre de vaccination")


@pytest.fixture
def mapper(db, activite_cdv):
    def _factory(record, today=None):
        return VaccinationMapper(record, activite_cdv, today=today)

    return _factory


def test_unpublish_closed_erp(neufchateau, sample_record_ok, activite_cdv):
    fetcher = FakeJsonFetcher([sample_record_ok])
    today = datetime(2021, 1, 1)
    mapper = VaccinationMapper
    Importer(
        "", fetcher=fetcher, mapper=mapper, activite=activite_cdv, today=today
    ).process()

    # reimport the same record, but this time it's closed
    sample_closed = sample_record_ok.copy()
    sample_closed["properties"]["c_date_fermeture"] = "2021-01-01"

    fetcher = FakeJsonFetcher([sample_closed])
    today = datetime(2021, 1, 2)
    mapper = VaccinationMapper
    Importer(
        "", fetcher=fetcher, mapper=mapper, activite=activite_cdv, today=today
    ).process()

    erp = Erp.objects.get(source_id=sample_record_ok["properties"]["c_gid"])
    assert erp.published is False


def test_intercept_sql_errors(mapper, neufchateau, sample_record_ok):
    long_cp_record = sample_record_ok.copy()
    long_cp_record["properties"]["c_com_cp"] = "12345 / 54321"

    with pytest.raises(DataError):
        erp, _ = mapper(long_cp_record).process()
        erp.save()
