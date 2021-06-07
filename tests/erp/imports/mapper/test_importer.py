import pytest

from datetime import datetime
from django.db import DataError

from erp.imports.mapper import SkippedRecord


def test_unpublish_closed_erp(mapper, neufchateau, sample_record_ok, capsys):
    erp1 = mapper(sample_record_ok, today=datetime(2021, 1, 1)).process()
    erp1.save()

    # reimport the same record, but this time it's closed
    sample_closed = sample_record_ok.copy()
    sample_closed["properties"]["c_date_fermeture"] = "2021-01-01"

    erp, reason = mapper(sample_closed, today=datetime(2021, 1, 2)).process()

    assert "fermé" in reason
    assert erp1.published is False


def test_intercept_sql_errors(mapper, neufchateau, sample_record_ok):
    long_cp_record = sample_record_ok.copy()
    long_cp_record["properties"]["c_com_cp"] = "12345 / 54321"

    with pytest.raises(DataError):
        erp = mapper(long_cp_record).process()
        erp.save()
