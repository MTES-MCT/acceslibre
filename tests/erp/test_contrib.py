import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.messages.constants import SUCCESS
from django.test import Client
from django.urls import reverse
from reversion.models import Version

from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory, UserFactory

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


def test_empty_search_results(client):
    response = client.get(
        reverse("contrib_global_search"),
        data={
            "what": "",
            "code": "",
            "activite": "",
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


@pytest.mark.django_db
def test_contrib_start_global_search_with_existing(client, mocker, akei_result, mairie_jacou_result):
    commune = CommuneFactory(nom="Jacou")
    mairie = ActiviteFactory(nom="Mairie")
    user = UserFactory()

    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    obj_erp = ErpFactory(
        nom="Mairie - Jacou",
        siret=None,
        numero="2",
        voie="place de la Mairie",
        code_postal="34830",
        commune="Jacou",
        commune_ext=commune,
        geom=Point((3.9047933, 43.6648217)),
        activite=mairie,
        published=True,
        user=user,
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
    assert all(
        [x in response.context["query"] for x in ("nom", "commune", "activite", "code_postal", "lat", "lon")]
    ), "Missing info for encode_provider_data"


@pytest.mark.django_db
def test_submitting_contrib_edit_info_form_without_info_does_no_trigger_save(django_app, activite_other):
    erp = AccessibiliteFactory(erp__published=True).erp
    CommuneFactory(nom=erp.commune)
    initial_updated_at = erp.updated_at
    assert Version.objects.get_for_object(erp).count() == 0

    url = reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug})
    page = django_app.get(url)
    edit_page_form = page.forms["contrib-edit-form"]
    response = edit_page_form.submit().follow()
    assert response.status_code == 200

    assert Version.objects.get_for_object(erp).count() == 0
    erp.refresh_from_db()
    assert erp.updated_at == initial_updated_at


@pytest.mark.django_db
def test_submitting_contrib_edit_info_form_with_info_does_trigger_save(django_app, activite_other):
    erp = AccessibiliteFactory(erp__published=True).erp
    CommuneFactory(nom=erp.commune)
    initial_updated_at = erp.updated_at
    assert Version.objects.get_for_object(erp).count() == 0

    url = reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug})
    page = django_app.get(url)
    edit_page_form = page.forms["contrib-edit-form"]
    edit_page_form["site_internet"] = "https://example.com"
    response = edit_page_form.submit().follow()
    assert response.status_code == 200

    assert Version.objects.get_for_object(erp).count() == 1
    erp.refresh_from_db()
    assert erp.updated_at > initial_updated_at

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level == SUCCESS
