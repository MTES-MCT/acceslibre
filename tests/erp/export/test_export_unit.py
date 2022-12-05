import csv
import os
from tempfile import NamedTemporaryFile
from typing import List

import pytest

from erp.export.export import export_schema_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.mappers import EtalabMapper
from erp.models import Erp


@pytest.fixture
def example_data(erp_with_a11y) -> List[Erp]:
    return [
        erp_with_a11y(
            "test 1",
            transport_station_presence=True,
            commentaire="simple commentaire",
        ),
        erp_with_a11y(
            "test 2",
            transport_station_presence=False,
            commentaire="simple commentaire 2",
        ),
    ]


@pytest.mark.skip(reason="Dependancies error.")
def test_export_to_csv(example_data):
    file = NamedTemporaryFile(suffix=".csv").name
    export_schema_to_csv(file, Erp.objects.all(), EtalabMapper)

    assert os.path.isfile(file) is True

    with open(file, "r") as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=EtalabMapper.headers())
        next(reader)  # Skip headers

        erp_0 = next(reader)
        assert erp_0["transport_station_presence"] == str(example_data[0].accessibilite.transport_station_presence)
        erp_1 = next(reader)
        assert erp_1["transport_station_presence"] == str(example_data[1].accessibilite.transport_station_presence)


@pytest.mark.skip(reason="Dependancies error.")
def test_generate_schema(db, activite):
    base = "erp/export/static/base-schema.json"
    outfile = "schema-test.json"
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.10/"

    generate_schema(base, outfile, repository)

    try:
        with open("schema-test.json", "r") as test_schema, open("erp/export/static/schema.json", "r") as actual_schema:
            assert test_schema.read().strip() == actual_schema.read().strip()
    finally:
        os.remove(test_schema.name)
