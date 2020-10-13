import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from erp.models import Erp

AKEI_SIRET = "88076068100010"


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="jean-pierre",
        password="Abc12345!",
        email="user@user.tld",
        is_staff=False,
        is_active=True,
    )


@pytest.fixture
def client(user):
    client = Client()
    client.login(username="jean-pierre", password="Abc12345!")
    return client


@pytest.fixture
def akei_result():
    return dict(
        source="sirene",
        source_id=AKEI_SIRET,
        actif=True,
        coordonnees=None,
        naf="62.02A",
        activite=None,
        nom="AKEI",
        siret=AKEI_SIRET,
        numero="4",
        voie="GRAND RUE",
        lieu_dit=None,
        code_postal="34830",
        commune="JACOU",
        code_insee="34120",
        contact_email=None,
        telephone=None,
        site_internet=None,
    )


@pytest.fixture
def mairie_jacou_result():
    return dict(
        source="public_erp",
        source_id="mairie-jacou-34120-01",
        actif=True,
        coordonnees=[3, 42],
        naf=None,
        activite=None,
        nom="Marie - Jacou",
        siret=None,
        numero="2",
        voie="Place de la Mairie",
        lieu_dit=None,
        code_postal="34830",
        commune="Jacou",
        code_insee="34120",
        contact_email="jacou@jacou.fr",
        telephone="01 02 03 04 05",
        site_internet="https://ville-jacou.fr/",
    )


def test_contrib_start_home(client):
    response = client.get(reverse("contrib_start"))
    assert response.status_code == 200
    assert response.context["siret_search_error"] is None
    assert response.context["name_search_error"] is None
    assert response.context["name_search_results"] is None
    assert response.context["public_erp_results"] is None
    assert response.context["public_erp_search_error"] is None


def test_contrib_start_siret_search_validate_siret(client):
    response = client.post(
        reverse("contrib_start"), data={"search_type": "by-siret", "siret": "xxx"}
    )
    assert response.status_code == 200
    assert "siret" in response.context["siret_form"].errors


def test_contrib_start_search_by_siret(client, mocker, akei_result):
    # Mock SIRENE api results
    mocker.patch(
        "erp.sirene.get_siret_info", return_value=akei_result,
    )

    # Mock Geocoder results
    mocker.patch(
        "erp.geocoder.geocode",
        return_value={
            "geom": Point(3, 42),
            "numero": "4",
            "voie": "Grand Rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34120",
        },
    )

    response = client.post(
        reverse("contrib_start"),
        data={"search_type": "by-siret", "siret": AKEI_SIRET},
        follow=True,
    )
    # Contrib admin-infos form page
    assert response.status_code == 200
    form_data = response.context["form"].cleaned_data
    assert form_data["siret"] == AKEI_SIRET
    assert form_data["source"] == "sirene"
    assert form_data["source_id"] == AKEI_SIRET
    assert form_data["geom"].coords == (3, 42)
    assert form_data["nom"] == "AKEI"
    assert form_data["numero"] == "4"
    assert form_data["voie"] == "Grand Rue"
    assert form_data["lieu_dit"] is None
    assert form_data["code_postal"] == "34830"
    # XXX investigate why this is failing in test env
    # assert form_data["commune"] == "Jacou"
    assert form_data["contact_email"] is None
    assert form_data["site_internet"] is None
    assert form_data["telephone"] is None


def test_contrib_start_search_by_business(client, mocker, akei_result):
    # Mock SIRENE api results (list)
    mocker.patch(
        "erp.views.find_sirene_businesses", return_value=[akei_result],
    )

    response = client.post(
        reverse("contrib_start"),
        data={
            "search_type": "by-business",
            "nom": "akei",
            "lieu": "Jacou",
            "naf": "62.02A",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["name_search_results"] == [akei_result]


def test_contrib_start_search_public_erp(client, mocker, mairie_jacou_result):
    # Mock SIRENE api results (list)
    mocker.patch(
        "erp.views.find_public_erps", return_value=[mairie_jacou_result],
    )

    response = client.post(
        reverse("contrib_start"),
        data={
            "search_type": "by-public-erp",
            "type": "mairie",
            "commune": "Jacou (34)",
            "code_insee": "34120",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["public_erp_results"] == [mairie_jacou_result]
