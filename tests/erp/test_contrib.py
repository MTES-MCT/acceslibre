import pytest

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from erp.models import Accessibilite, Erp

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
        source="entreprise_api",
        source_id="12345",
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


def test_contrib_start_global_search(client, mocker, akei_result, mairie_jacou_result):
    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    response = client.get(
        reverse("contrib_global_search"),
        data={
            "commune_search": "Jacou (34)",
            "code_insee": "34120",
            "search": "mairie",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["results"] == [mairie_jacou_result, akei_result]


def test_claim(client, user):
    erp = Erp.objects.create(nom="test", published=True)

    response = client.get(reverse("contrib_claim", kwargs={"erp_slug": erp.slug}))
    assert response.status_code == 200  # jean-pierre is logged in the client

    response = client.post(
        reverse("contrib_claim", kwargs={"erp_slug": erp.slug}),
        data={"ok": "on"},
        follow=True,
    )

    erp.refresh_from_db()
    assert response.context["form"].errors == {}
    assert erp.user == user
    assert erp.user_type == Erp.USER_ROLE_GESTIONNAIRE
