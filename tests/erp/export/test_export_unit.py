import csv
import os
from io import StringIO
from typing import List

import pytest

from erp.export.export import export_schema_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.utils import map_erps_to_json_schema
from erp.export.mappers import EtalabMapper
from erp.models import Accessibilite, Erp


def create_test_erp(name, **a11y_data):
    erp = Erp.objects.create(nom=name)
    if a11y_data:
        Accessibilite.objects.create(erp=erp, **a11y_data)
    else:
        # simulate the case we have a non-a11y field filled
        Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
    return erp


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
    first_row = EtalabMapper.headers()
    headers, mapped_data = map_erps_to_json_schema(example_data, EtalabMapper)
    file = StringIO()

    export_schema_to_csv(file, example_data, EtalabMapper)
    file.seek(0)
    reader = csv.DictReader(file, fieldnames=first_row)
    next(reader)  # Skip headers

    erp_0 = next(reader)
    assert erp_0["transport_station_presence"] == str(
        mapped_data[0].transport_station_presence
    )
    erp_1 = next(reader)
    assert erp_1["transport_station_presence"] == str(
        mapped_data[1].transport_station_presence
    )

    # Validate data with schema


def test_generate_schema():
    base = "erp/export/static/base-schema.json"
    outfile = "schema-test.json"
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.1/"

    generate_schema(base, outfile, repository)

    try:
        with open("schema-test.json", "r") as test_schema, open(
            "erp/export/static/schema.json", "r"
        ) as actual_schema:
            assert test_schema.read().strip() == actual_schema.read().strip()
    finally:
        os.remove(test_schema.name)
