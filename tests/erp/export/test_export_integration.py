# TI: test csv file writing
# TI: check frictionless validation with http call
# TI: export to data.gouv
import os
from pathlib import Path

import frictionless
import pytest

from erp.export.export import export_to_csv
from erp.export.mappers import map_erp_to_json_schema
from erp.models import Erp


@pytest.mark.integtest
@pytest.mark.django_db
def test_csv_creation(db):
    with open("export-test.csv", "w", newline="") as csv_file:
        erps = Erp.objects.having_a11y_data().all()
        headers, mapped_data = map_erp_to_json_schema(erps)
        export_to_csv(csv_file, headers, mapped_data)

        assert Path("export.csv").exists() is True
        assert frictionless.validate_package()

    os.remove(csv_file.name)
