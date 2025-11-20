import csv
import hashlib
import io
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import management
from django.core.management import call_command

from erp.export.export import export_schema_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.mappers import EtalabMapper
from erp.export.tasks import generate_csv_file
from erp.models import Erp, ExternalSource
from tests.factories import ActiviteFactory, ErpFactory, ExternalSourceFactory


@pytest.mark.django_db
def test_csv_creation():
    ErpFactory(accessibilite__entree_porte_presence=True)
    dest_path = NamedTemporaryFile(suffix=".csv").name

    try:
        erps = Erp.objects.having_a11y_data().all()[0:10]
        export_schema_to_csv(dest_path, erps, EtalabMapper)

        assert Path(dest_path).exists() is True
    finally:
        os.remove(dest_path)


@pytest.mark.django_db
def test_export_command(mocker, settings):
    settings.DATAGOUV_API_KEY = "fake"  # To pass the check before uploading
    mocker.patch("requests.post")
    activity = ActiviteFactory(nom="Boulangerie")
    erp = ErpFactory(
        nom="Aux bons croissants",
        code_postal="34830",
        commune="Jacou",
        numero=4,
        voie="grand rue",
        siret="52128577500016",
        geom=Point(3.9047933, 43.6648217),
        activite=activity,
        accessibilite__accueil_audiodescription_presence=True,
        accessibilite__accueil_audiodescription=["avec_app"],
        accessibilite__accueil_chambre_nombre_accessibles=12,
        accessibilite__accueil_chambre_douche_plain_pied=True,
        accessibilite__accueil_chambre_douche_siege=True,
        accessibilite__accueil_chambre_douche_barre_appui=True,
        accessibilite__accueil_chambre_sanitaires_barre_appui=False,
        accessibilite__accueil_chambre_sanitaires_espace_usage=True,
        accessibilite__accueil_chambre_numero_visible=True,
        accessibilite__accueil_chambre_equipement_alerte=False,
        accessibilite__accueil_chambre_accompagnement=True,
        accessibilite__sanitaires_presence=True,
        accessibilite__sanitaires_adaptes=False,
        accessibilite__commentaire="foo",
        accessibilite__entree_porte_presence=True,
        accessibilite__entree_reperage=True,
    )
    ExternalSourceFactory(source=ExternalSource.SOURCE_RNB, source_id="123456789", erp=erp)

    assert Erp.objects.count(), "We should have ERPs in DB"

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
        "",
        "",
        "",
        "",
        "[]",
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
        "123456789",
    ]

    management.call_command("export_to_datagouv", "--skip-upload")
    assert os.path.isfile("acceslibre.csv")
    assert os.stat("acceslibre.csv").st_size > 0
    with open("acceslibre.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 90, "New exported field or missing field in export"
        assert erp_csv == expected

    assert os.path.isfile("acceslibre-with-web-url.csv")
    assert os.stat("acceslibre-with-web-url.csv").st_size > 0
    with open("acceslibre-with-web-url.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 91, "New exported field or missing field in export"
        assert erp_csv == expected + ["http://testserver/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/"]

    os.unlink("acceslibre-with-web-url.csv")


@pytest.mark.django_db
def test_export_failure(mocker, settings):
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
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.18/"

    generate_schema(base, outfile, repository)

    try:
        with open(outfile, "r") as test_schema, open("erp/export/static/schema.json", "r") as actual_schema:
            assert json.loads(test_schema.read()) == json.loads(actual_schema.read().strip())
    finally:
        os.remove(test_schema.name)


@pytest.mark.django_db
@patch("core.mailer.BrevoMailer.send_email")
@patch("boto3.client")
def test_generate_csv_export(mock_boto_client, mock_send_email):
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.generate_presigned_url.return_value = "https://mock-s3-url.com/download.csv"

    ErpFactory(nom="Mairie1", with_accessibility=True)
    ErpFactory(nom="Mairie2", with_accessibility=True)
    ErpFactory(nom="Boulangerie", with_accessibility=True)

    generate_csv_file(query_params="what=Mairie", user_email="user@example.com", username="User Name")

    put_object_call = mock_s3.put_object.call_args
    filename = put_object_call[1]["Key"]
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    email_hash = hashlib.sha256("user@example.com".encode()).hexdigest()[:10]
    expected_filename = f"export_{now}_{email_hash}.csv"
    assert filename == expected_filename

    csv_content = put_object_call[1]["Body"]
    csv_reader = csv.reader(io.StringIO(csv_content))
    header = next(csv_reader)

    assert "name" in header, "The 'name' header is missing."
    assert "user_type" in header
    assert "username" in header

    rows = list(csv_reader)
    assert len(rows) == 2, "There should be at 2 rows of data."

    names = [row[header.index("name")] for row in rows]
    assert "Mairie1" in names, "The row with 'Mairie1' is missing."
    assert "Mairie2" in names, "The row with 'Mairie2' is missing."

    mock_s3.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={
            "Bucket": settings.S3_EXPORT_BUCKET_NAME,
            "Key": expected_filename,
        },
        ExpiresIn=86400,
    )

    mock_send_email.assert_called_once_with(
        to_list="user@example.com",
        template="export-results",
        context={"file_url": "https://mock-s3-url.com/download.csv", "username": "User Name"},
    )


CURRENT_TIME = datetime(2024, 10, 1, tzinfo=timezone.utc)


@patch("boto3.client")
@patch("datetime.datetime")
def test_clean_s3_export_bucket(mock_datetime, mock_boto_client):
    mock_datetime.now.return_value = CURRENT_TIME
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "file1.csv", "LastModified": CURRENT_TIME - timedelta(hours=26)},
            {"Key": "file2.csv", "LastModified": CURRENT_TIME - timedelta(hours=27)},
            {"Key": "file3.csv", "LastModified": CURRENT_TIME - timedelta(hours=24)},
        ]
    }

    mock_s3.delete_objects.return_value = {"Deleted": [{"Key": "file1.csv"}, {"Key": "file2.csv"}]}

    call_command("clean_S3_export_bucket")

    mock_s3.list_objects_v2.assert_called_once_with(Bucket=settings.S3_EXPORT_BUCKET_NAME)

    delete_call = mock_s3.delete_objects.call_args[1]
    files_to_delete = delete_call["Delete"]["Objects"]

    assert len(files_to_delete) == 2
    assert {"Key": "file1.csv"} in files_to_delete
    assert {"Key": "file2.csv"} in files_to_delete
    assert {"Key": "file3.csv"} not in files_to_delete
