import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import requests
from django.core import management
from frictionless import validate_resource, Resource, validate_schema, Schema

from erp.export.export import export_schema_to_csv
from erp.export.mappers import EtalabMapper
from erp.models import Erp


def test_csv_creation(db):
    dest_path = NamedTemporaryFile(suffix=".csv").name

    try:
        erps = Erp.objects.having_a11y_data().all()[0:10]
        export_schema_to_csv(dest_path, erps, EtalabMapper)

        assert Path(dest_path).exists() is True
    finally:
        os.remove(dest_path)


def test_export_command(mocker, db, settings):
    settings.DATAGOUV_API_KEY = "fake"  # To pass the check before uploading
    mocker.patch("requests.post")

    management.call_command("export_to_datagouv")
    assert os.path.isfile("acceslibre.csv")
    assert os.stat("acceslibre.csv").st_size > 0
    os.unlink("acceslibre.csv")


def test_export_failure(mocker, db, settings):
    settings.DATAGOUV_API_KEY = "fake"  # To pass the check before uploading
    mocker.patch(
        "requests.post",
        side_effect=requests.RequestException("KO"),
    )
    from erp.management.commands.export_to_datagouv import logger

    with pytest.raises(management.CommandError) as err:
        management.call_command("export_to_datagouv")

    if os.path.isfile("acceslibre.csv"):
        os.unlink("acceslibre.csv")
    assert "Erreur lors de l'upload" in str(err.value)


# def test_schema_validation():
#     schema = Schema("erp/export/static/schema.json")
#     resource = Resource(
#         "erp/export/static/exemple-valide.csv",
#         schema=schema,
#     )
#     result_schema = validate_schema(schema)
#     result_resource = validate_resource(resource)
#     assert result_schema.get("valid") is True
#     assert result_resource.get("valid") is True
