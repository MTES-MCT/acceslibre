import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from erp.models import Activite, Erp

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
        coordonnees=[3, 42],
        naf=None,
        activite=None,
        nom="Mairie - Jacou",
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


def test_empty_search_results(data, client):
    response = client.get(
        reverse("contrib_global_search"),
        data={
            "what": "",
            "code": "",
        },
    )
    assert response.status_code == 200


def test_contrib_start_global_search(client, mocker, akei_result, mairie_jacou_result):
    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    response = client.get(
        reverse("contrib_global_search"),
        data={
            "code": "34120",
            "what": "mairie",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["results"] == [mairie_jacou_result, akei_result]


def test_contrib_start_global_search_with_existing(client, data, mocker, akei_result, mairie_jacou_result):
    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    mairie = Activite.objects.create(nom="Mairie")
    obj_erp = Erp.objects.create(
        nom="Mairie - Jacou",
        siret=None,
        numero="2",
        voie="place de la Mairie",
        code_postal="34830",
        commune="Jacou",
        commune_ext=data.jacou,
        geom=Point((3.9047933, 43.6648217)),
        activite=mairie,
        published=True,
        user=data.niko,
    )

    response = client.get(
        reverse("contrib_global_search"),
        data={
            "code": "34120",
            "what": "mairie",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert response.context["results"] == [akei_result]
    assert len(response.context["results_bdd"]) == 1
    assert "exists" in response.context["results_bdd"][0]
    assert response.context["results_bdd"][0]["source"] == "acceslibre"
    assert response.context["results_bdd"][0]["id"] == obj_erp.id


def test_claim(client, user, data):
    erp = Erp.objects.create(user=user, nom="test", commune="lyon", published=True, geom=Point(0, 0))

    user.stats.refresh_from_db()
    initial_nb_attributed = user.stats.nb_erp_attributed

    response = client.post(reverse("contrib_claim", kwargs={"erp_slug": erp.slug}), follow=True)
    assert response.redirect_chain == [
        ("/contrib/edit-infos/test/", 302)
    ], "ERP is already attributed, should redirect to edition"

    user.stats.refresh_from_db()
    assert user.stats.nb_erp_attributed == initial_nb_attributed

    erp.user = None
    erp.save()

    response = client.post(reverse("contrib_claim", kwargs={"erp_slug": erp.slug}), data={"ok": False}, follow=True)
    assert response.context["form"].is_valid() is False
    erp.refresh_from_db()
    assert erp.user is None, "User has not certified he is the owner and did not check the tickbox."

    user.stats.refresh_from_db()
    assert user.stats.nb_erp_attributed == initial_nb_attributed

    response = client.post(reverse("contrib_claim", kwargs={"erp_slug": erp.slug}), data={"ok": True}, follow=True)
    erp.refresh_from_db()
    assert erp.user == user
    assert erp.user_type == Erp.USER_ROLE_GESTIONNAIRE

    user.stats.refresh_from_db()
    assert user.stats.nb_erp_attributed == initial_nb_attributed + 1
