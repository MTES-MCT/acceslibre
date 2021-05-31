import os
from pathlib import Path

from frictionless import validate_resource, Resource

from erp.export.export import export_schema_to_csv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


def test_csv_creation(db):
    dest_path = "export-test.csv"
    try:
        with open(dest_path, "w", newline="") as csv_file:
            erps = Erp.objects.having_a11y_data().all()[0:10]
            export_schema_to_csv(csv_file, erps, EtalabMapper)

        assert Path(dest_path).exists() is True

        resource = Resource(
            "erp/export/static/exemple-valide.csv",
            schema="erp/export/static/schema.json",
        )
        result = validate_resource(resource)
        assert result.get("errors") == []
    finally:
        os.remove(dest_path)
