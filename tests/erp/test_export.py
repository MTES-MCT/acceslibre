import csv
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import ANY

import pytest
import requests
from django.core import management

from erp.export.export import export_schema_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.mappers import EtalabMapper
from erp.models import Erp


def test_csv_creation(data):
    dest_path = NamedTemporaryFile(suffix=".csv").name

    try:
        erps = Erp.objects.having_a11y_data().all()[0:10]
        export_schema_to_csv(dest_path, erps, EtalabMapper)

        assert Path(dest_path).exists() is True
    finally:
        os.remove(dest_path)


def test_export_command(mocker, data, settings):
    settings.DATAGOUV_API_KEY = "fake"  # To pass the check before uploading
    mocker.patch("requests.post")

    # tweak the existing ERP to have some fields to export
    data.erp.accessibilite.accueil_audiodescription_presence = True
    data.erp.accessibilite.accueil_audiodescription = ["avec_app"]
    data.erp.accessibilite.accueil_chambre_nombre_accessibles = 12
    data.erp.accessibilite.accueil_chambre_douche_plain_pied = True
    data.erp.accessibilite.accueil_chambre_douche_siege = True
    data.erp.accessibilite.accueil_chambre_douche_barre_appui = True
    data.erp.accessibilite.accueil_chambre_sanitaires_barre_appui = False
    data.erp.accessibilite.accueil_chambre_sanitaires_espace_usage = True
    data.erp.accessibilite.accueil_chambre_numero_visible = True
    data.erp.accessibilite.accueil_chambre_equipement_alerte = False
    data.erp.accessibilite.accueil_chambre_accompagnement = True
    data.erp.accessibilite.save()

    assert Erp.objects.all(), "No ERP"

    expected = [
        ANY,
        "Aux bons croissants",
        "34830",
        "Jacou",
        "4",
        "grand rue",
        "",
        "",
        "52128577500016",
        "Boulangerie",
        "",
        "",
        "3.9047933",
        "43.6648217",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "True",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "True",
        "",
        "",
        "",
        "",
        "True",
        '["avec_app"]',
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "12",
        "True",
        "True",
        "True",
        "False",
        "True",
        "True",
        "False",
        "True",
        "",
        "True",
        "False",
        "",
        "",
        "",
        "",
    ]

    management.call_command("export_to_datagouv", "--skip-upload")
    assert os.path.isfile("acceslibre.csv")
    assert os.stat("acceslibre.csv").st_size > 0
    with open("acceslibre.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 82, "New exported field or missing field in export"
        assert erp_csv == expected

    assert os.path.isfile("acceslibre-with-web-url.csv")
    assert os.stat("acceslibre-with-web-url.csv").st_size > 0
    with open("acceslibre-with-web-url.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 83, "New exported field or missing field in export"
        assert erp_csv == expected + ["http://testserver/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/"]

    os.unlink("acceslibre-with-web-url.csv")


def test_export_failure(mocker, data, settings):
    settings.DATAGOUV_API_KEY = "fake"  # To pass the check before uploading
    mocker.patch(
        "requests.post",
        side_effect=requests.RequestException("KO"),
    )

    with pytest.raises(management.CommandError) as err:
        management.call_command("export_to_datagouv")

    if os.path.isfile("acceslibre.csv"):
        os.unlink("acceslibre.csv")
    assert "Erreur lors de l'upload" in str(err.value)


def test_generate_schema(db, activite):
    base = "erp/export/static/base-schema.json"
    outfile = "schema-test.json"
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.15/"

    generate_schema(base, outfile, repository)

    try:
        with open(outfile, "r") as test_schema, open("erp/export/static/schema.json", "r") as actual_schema:
            assert json.loads(test_schema.read()) == json.loads(actual_schema.read().strip())
    finally:
        os.remove(test_schema.name)
