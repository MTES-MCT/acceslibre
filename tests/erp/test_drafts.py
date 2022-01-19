import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from erp import schema
from erp.models import Erp

from tests.utils import assert_redirect


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_result(data):
    return {
        "exists": data.erp,
        "source": "entreprise_api",
        "source_id": "63015890",
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
        "activite": None,
        "nom": "Akei",
        "siret": "88076068100010",
        "numero": "4",
        "voie": "Grand Rue",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "34120",
        "contact_email": None,
        "telephone": None,
        "site_internet": None,
    }


@pytest.fixture
def test_response(client, mocker, sample_result):
    def _factory(user_to_log_in):
        mocker.patch("erp.provider.search.global_search", return_value=[sample_result])
        client.force_login(user_to_log_in)
        return client.get(
            reverse("contrib_global_search")
            + "?search=croissants&code_insee=34120&commune_search=Jacou+%2834%2C+Hérault%29"
        ).content.decode()

    return _factory


def test_owner_draft_listed(data, test_response):
    data.erp.published = False
    data.erp.save()
    response_content = test_response(data.niko)

    assert "Existe dans vos brouillons" in response_content
    assert "Reprendre votre brouillon" in response_content


def test_owner_published_listed(data, test_response):
    data.erp.published = True
    data.erp.save()
    response_content = test_response(data.niko)

    assert "Vous avez créé cette fiche" in response_content
    assert "Modifier cet établissement" in response_content


def test_user_draft_listed(data, test_response):
    data.erp.published = False
    data.erp.save()
    response_content = test_response(data.sophie)

    assert "Existe à l'état de brouillon" in response_content
    assert (
        "Cet établissement est pris en charge par un autre contributeur"
        in response_content
    )


def test_user_published_listed(data, test_response):
    data.erp.published = True
    data.erp.save()
    response_content = test_response(data.sophie)

    assert "Existe déjà dans la base" in response_content
    assert "Voir cet établissement" in response_content
