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
from freezegun import freeze_time

from erp.export.export import export_schema_to_csv
from erp.export.generate_schema import generate_schema
from erp.export.mappers import EtalabMapper
from erp.export.s3 import DATAGOUV_EXPORT_PREFIX, select_datagouv_files_to_delete
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
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "True",
        "False",
        "",
        "",
        "",
        "",
        "False",
        "123456789",
    ]

    management.call_command("export_to_datagouv", "--skip-upload")
    assert os.path.isfile("acceslibre.csv")
    assert os.stat("acceslibre.csv").st_size > 0
    with open("acceslibre.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 101, "New exported field or missing field in export"
        assert erp_csv == expected

    assert os.path.isfile("acceslibre-with-web-url.csv")
    assert os.stat("acceslibre-with-web-url.csv").st_size > 0
    with open("acceslibre-with-web-url.csv", "r") as f:
        reader = csv.reader(f)
        header, erp_csv = iter(reader)
        assert len(header) == 103, "New exported field or missing field in export"
        assert erp_csv == expected + [
            "http://testserver/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/",
            '<div id="widget-a11y-container" '
            f'data-pk="{erp.uuid}" '
            'data-baseurl="http://testserver"></div>\n'
            '<a href="#" aria-haspopup="dialog" '
            f'data-erp-pk="{erp.uuid}" aria-controls="dialog" '
            'data-owner="acceslibre">Accessibilité</a>\n'
            '<script src="http://testserver/static/js/widget.js" '
            'type="text/javascript" async="true"></script>',
        ]

    os.unlink("acceslibre-with-web-url.csv")


@pytest.mark.django_db
def test_export_xml_to_s3_xml_content(mocker, settings):
    settings.S3_EXPORT_BUCKET_NAME = "test-bucket"
    settings.S3_EXPORT_BUCKET_ENDPOINT_URL = "https://fake-s3.example.com"
    settings.SITE_HOST = "testserver"

    activity = ActiviteFactory(nom="Boulangerie", id=1)
    ErpFactory(
        nom="Aux bons croissants",
        code_postal="34830",
        commune="Jacou",
        geom=Point(3.9047933, 43.6648217),
        activite=activity,
        published=True,
    )

    uploaded_parts = []

    mock_s3 = MagicMock()
    mock_s3.create_multipart_upload.return_value = {"UploadId": "fake-upload-id"}
    mock_s3.upload_part.side_effect = lambda **kwargs: (
        uploaded_parts.append(kwargs["Body"]) or {"ETag": f"etag-{kwargs['PartNumber']}"}
    )
    mock_s3.generate_presigned_url.return_value = "https://fake-url.example.com/export.xml"

    mocker.patch("boto3.client", return_value=mock_s3)

    management.call_command("export_XML_to_s3")

    full_xml = b"".join(uploaded_parts)
    assert b"Aux bons croissants" in full_xml
    assert b"Jacou" in full_xml
    assert b"34830" in full_xml
    assert b"3.9047933" in full_xml
    assert b"43.6648217" in full_xml
    assert b"geom" not in full_xml  # geom field should be excluded, see ErpXMLSerializer.Meta
    assert b'<?xml version="1.0" encoding="utf-8"?>' in full_xml
    assert full_xml.strip().endswith(b"</root>")


@pytest.mark.django_db
def test_export_xml_to_s3_aborts_on_error(mocker, settings):
    """Check that multipart upload is aborted when an error occurs"""
    settings.S3_EXPORT_BUCKET_NAME = "test-bucket"
    settings.S3_EXPORT_BUCKET_ENDPOINT_URL = "https://fake-s3.example.com"
    settings.SITE_HOST = "testserver"

    activity = ActiviteFactory(nom="Boulangerie", id=1)
    ErpFactory(
        nom="Aux bons croissants",
        geom=Point(3.9047933, 43.6648217),
        activite=activity,
        published=True,
    )

    mock_s3 = MagicMock()
    mock_s3.create_multipart_upload.return_value = {"UploadId": "fake-upload-id"}
    mock_s3.upload_part.side_effect = Exception("S3 failure")

    mocker.patch("boto3.client", return_value=mock_s3)

    with pytest.raises(Exception, match="S3 failure"):
        management.call_command("export_XML_to_s3")

    mock_s3.abort_multipart_upload.assert_called_once_with(
        Bucket="test-bucket",
        Key=ANY,
        UploadId="fake-upload-id",
    )


@pytest.mark.django_db
def test_export_xml_to_s3_filters_activities(mocker, settings):
    settings.S3_EXPORT_BUCKET_NAME = "test-bucket"
    settings.S3_EXPORT_BUCKET_ENDPOINT_URL = "https://fake-s3.example.com"
    settings.SITE_HOST = "testserver"

    activity_included = ActiviteFactory(nom="Boulangerie", id=1)
    activity_excluded = ActiviteFactory(nom="Autre", id=9999)

    ErpFactory(nom="ERP included", geom=Point(3.9, 43.6), activite=activity_included, published=True)
    ErpFactory(nom="ERP excluded", geom=Point(3.9, 43.6), activite=activity_excluded, published=True)

    uploaded_parts = []
    mock_s3 = MagicMock()
    mock_s3.create_multipart_upload.return_value = {"UploadId": "fake-upload-id"}
    mock_s3.upload_part.side_effect = lambda **kwargs: (
        uploaded_parts.append(kwargs["Body"]) or {"ETag": f"etag-{kwargs['PartNumber']}"}
    )
    mock_s3.generate_presigned_url.return_value = "https://fake-url.example.com/export.xml"

    mocker.patch("boto3.client", return_value=mock_s3)

    management.call_command("export_XML_to_s3")

    full_xml = b"".join(uploaded_parts)
    assert b"ERP included" in full_xml
    assert b"ERP excluded" not in full_xml


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
    repository = "https://github.com/MTES-MCT/acceslibre-schema/raw/v0.0.20/"

    generate_schema(base, outfile, repository)

    try:
        with open(outfile, "r") as test_schema, open("erp/export/static/schema.json", "r") as actual_schema:
            assert json.loads(test_schema.read()) == json.loads(actual_schema.read().strip())
    finally:
        os.remove(test_schema.name)


CURRENT_TIME = datetime(2024, 10, 1, tzinfo=timezone.utc)


@pytest.mark.django_db
@freeze_time(CURRENT_TIME)
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


def _first_of_month(dt):
    """Return the first moment of the month containing dt."""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@patch("boto3.client")
@freeze_time(CURRENT_TIME)
def test_clean_s3_export_bucket(mock_boto_client):
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


@patch("boto3.client")
@freeze_time(CURRENT_TIME)
def test_clean_s3_export_bucket_keeps_xml_8_days(mock_boto_client):
    """XML files should only be deleted after 8 days, not 25 hours like other files."""
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "export.xml", "LastModified": CURRENT_TIME - timedelta(days=9)},
            {"Key": "export2.xml", "LastModified": CURRENT_TIME - timedelta(days=7)},
        ]
    }

    call_command("clean_S3_export_bucket")

    delete_call = mock_s3.delete_objects.call_args[1]
    files_to_delete = delete_call["Delete"]["Objects"]

    assert files_to_delete == [{"Key": "export.xml"}]


@patch("boto3.client")
@freeze_time(CURRENT_TIME)
def test_clean_s3_export_bucket_datagouv_prefix_recent_files_kept(mock_boto_client):
    """Datagouv files younger than 30 days should never be deleted."""
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}acceslibre_1.csv", "LastModified": CURRENT_TIME - timedelta(days=1)},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}acceslibre_29.csv", "LastModified": CURRENT_TIME - timedelta(days=29)},
        ]
    }

    call_command("clean_S3_export_bucket")

    mock_s3.delete_objects.assert_not_called()


@patch("boto3.client")
@freeze_time(CURRENT_TIME)
def test_clean_s3_export_bucket_datagouv_prefix_old_files_kept_one_per_month(mock_boto_client):
    """
    Beyond 30 days, only one file per month should be kept (the oldest one of that
    month), the rest must be deleted.
    """
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    # Base date guaranteed to be >30 days before CURRENT_TIME, regardless of its actual value
    month_1 = _first_of_month(CURRENT_TIME - timedelta(days=200))
    jan_early = month_1 + timedelta(days=2)
    jan_mid = month_1 + timedelta(days=14)
    jan_late = month_1 + timedelta(days=27)  # safe: every month has at least 28 days

    month_2 = _first_of_month(month_1 + timedelta(days=32))  # guarantees a different month
    feb = month_2 + timedelta(days=4)

    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_early.csv", "LastModified": jan_early},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_mid.csv", "LastModified": jan_mid},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_late.csv", "LastModified": jan_late},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}feb.csv", "LastModified": feb},
        ]
    }

    call_command("clean_S3_export_bucket")

    delete_call = mock_s3.delete_objects.call_args[1]
    files_to_delete = delete_call["Delete"]["Objects"]

    # Only the oldest file of each month is kept: jan_early and feb
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_mid.csv"} in files_to_delete
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_late.csv"} in files_to_delete
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}jan_early.csv"} not in files_to_delete
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}feb.csv"} not in files_to_delete
    assert len(files_to_delete) == 2


@patch("boto3.client")
@freeze_time(CURRENT_TIME)
def test_clean_s3_export_bucket_mixed_prefixes(mock_boto_client):
    """Ensure the 3 retention policies (25h, 8d for xml, 30d+1/month for datagouv) coexist without interference."""
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    # Only file in its "month" -> kept
    old_datagouv = CURRENT_TIME - timedelta(days=200)

    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "search_export.csv", "LastModified": CURRENT_TIME - timedelta(hours=26)},
            {"Key": "datatourisme.xml", "LastModified": CURRENT_TIME - timedelta(days=9)},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}recent.csv", "LastModified": CURRENT_TIME - timedelta(days=2)},
            {"Key": f"{DATAGOUV_EXPORT_PREFIX}old.csv", "LastModified": old_datagouv},
        ]
    }

    call_command("clean_S3_export_bucket")

    delete_call = mock_s3.delete_objects.call_args[1]
    files_to_delete = delete_call["Delete"]["Objects"]

    assert {"Key": "search_export.csv"} in files_to_delete
    assert {"Key": "datatourisme.xml"} in files_to_delete
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}recent.csv"} not in files_to_delete
    assert {"Key": f"{DATAGOUV_EXPORT_PREFIX}old.csv"} not in files_to_delete
    assert len(files_to_delete) == 2


def test_select_datagouv_files_to_delete_empty():
    """No objects, nothing to delete."""
    assert select_datagouv_files_to_delete([], CURRENT_TIME) == []


def test_select_datagouv_files_to_delete_all_recent():
    """All objects younger than 30 days should be kept."""
    objects = [
        {"Key": "a.csv", "LastModified": CURRENT_TIME - timedelta(days=1)},
        {"Key": "b.csv", "LastModified": CURRENT_TIME - timedelta(days=29)},
    ]
    assert select_datagouv_files_to_delete(objects, CURRENT_TIME) == []


def test_select_datagouv_files_to_delete_boundary_exactly_30_days():
    """
    A file exactly 30 days old must NOT be considered 'old' yet (the comparison
    must use strict < and not <=).
    """
    objects = [
        {"Key": "boundary.csv", "LastModified": CURRENT_TIME - timedelta(days=30)},
    ]
    assert select_datagouv_files_to_delete(objects, CURRENT_TIME) == []


def test_select_datagouv_files_to_delete_keeps_oldest_per_month():
    """Among old files sharing the same month, only the oldest one is kept."""
    # Anchor to the start of a month guaranteed to be >30 days before CURRENT_TIME,
    # then offset within that same month so d1/d2/d3 never cross a month boundary.
    month_start = _first_of_month(CURRENT_TIME - timedelta(days=200))
    d1 = month_start + timedelta(days=1)
    d2 = d1 + timedelta(days=10)
    d3 = d1 + timedelta(days=20)  # safe: every month has at least 28 days

    objects = [
        {"Key": "middle.csv", "LastModified": d2},
        {"Key": "first.csv", "LastModified": d1},
        {"Key": "last.csv", "LastModified": d3},
    ]

    result = select_datagouv_files_to_delete(objects, CURRENT_TIME)
    result_keys = {o["Key"] for o in result}

    assert "first.csv" not in result_keys
    assert result_keys == {"middle.csv", "last.csv"}
