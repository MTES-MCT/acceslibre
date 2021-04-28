import csv
from io import StringIO
from typing import List

import pytest

from erp.export.export import export_to_csv
from erp.export.mappers import map_erp_to_json_schema
from erp.export.models import ETALAB_SCHEMA_FIELDS
from erp.models import Erp
from tests.erp.test_managers import create_test_erp


@pytest.fixture
def example_data(db):
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


def test_export_to_csv(example_data: List[Erp]):
    # map
    first_row = ETALAB_SCHEMA_FIELDS
    headers, mapped_data = map_erp_to_json_schema(example_data)

    # write to csv
    file = StringIO()
    export_to_csv(file, headers, mapped_data)

    # assert correct csv values
    file.seek(0)
    reader = csv.DictReader(file, fieldnames=first_row)
    # Skip headers
    next(reader)
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

# Test updload data.gouv
