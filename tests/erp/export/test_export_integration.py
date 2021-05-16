# TI: test csv file writing
# TI: check frictionless validation with http call
# TI: automated export to data.gouv
import os
from pathlib import Path

import pytest
from frictionless import Package, validate_package

from erp.export.export import export_schema_to_csv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


@pytest.mark.django_db
def test_csv_creation(db):
    dest_path = "export-test.csv"
    try:
        with open(dest_path, "w", newline="") as csv_file:
            erps = Erp.objects.having_a11y_data().all()[0:10]
            export_schema_to_csv(csv_file, erps, EtalabMapper)

        assert Path(dest_path).exists() is True

        package = Package(descriptor="erp/export/static/schema.json")
        result = validate_package(package)
        assert result.get("errors") == []
    finally:
        os.remove(dest_path)


@pytest.mark.django_db
def test_check_modified_schema(db):
    # use stringio to test schema generation, then compare
    # maybe_new_schema = generate_schema()
    # assert maybe_new_schema == actual_schema
    ...
