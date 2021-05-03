import csv
import os
from io import StringIO
from typing import List

import pytest

from erp.export.export import export_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.mappers import map_erp_to_json_schema
from erp.export.models import ETALAB_SCHEMA_FIELDS
from erp.models import Erp
from tests.erp.test_managers import create_test_erp


@pytest.fixture
def example_data(db) -> List[Erp]:
    return [
        create_test_erp(
            "test 1", transport_station_presence=True, commentaire="simple commentaire"
        ),
        create_test_erp(
            "test 2",
            transport_station_presence=False,
            commentaire="simple commentaire 2",
        ),
    ]


def test_export_to_csv(example_data):
    first_row = ETALAB_SCHEMA_FIELDS
    headers, mapped_data = map_erp_to_json_schema(example_data)
    file = StringIO()

    export_to_csv(file, headers, mapped_data)
    file.seek(0)
    reader = csv.DictReader(file, fieldnames=first_row)
    next(reader)  # Skip headers

    erp_0 = next(reader)
    assert erp_0["transport_station_presence"] == str(
        mapped_data[0].transport_station_presence
    )
    assert erp_0["commentaire"] == str(mapped_data[0].commentaire)
    erp_1 = next(reader)
    assert erp_1["transport_station_presence"] == str(
        mapped_data[1].transport_station_presence
    )
    assert erp_1["commentaire"] == str(mapped_data[1].commentaire)

    # Validate data with schema


# Test/check invalid data ex: no accessibility object -> should be ignored
# Test transformed/mapped data

# Test upload data.gouv


def test_generate_schema():
    base = "erp/export/static/base-schema.json"
    outfile = "schema-test.json"
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.1/"

    generate_schema(base, outfile, repository)

    try:
        with open("schema-test.json", "r") as test_schema, open(
            "erp/export/static/schema.json", "r"
        ) as actual_schema:
            assert test_schema.read() == actual_schema.read()
    finally:
        os.remove(test_schema.name)
