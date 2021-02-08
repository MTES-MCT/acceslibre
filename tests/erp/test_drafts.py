import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from erp import schema
from erp.models import Erp

from tests.fixtures import data
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
        "actif": True,
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


def test_user_draft_listed(client, data, mocker, sample_result, capsys):
    data.erp.published = False
    data.erp.save()

    client.login(username="niko", password="Abc12345!")

    mocker.patch("erp.provider.search.global_search", return_value=[sample_result])

    response = client.get(
        reverse("contrib_global_search")
        + "?search=croissants&code_insee=34120&commune_search=Jacou+%2834%2C+Hérault%29&sources=pagesjaunes"
    )

    assert "Existe à l'état de brouillon" in response.content.decode()
    assert "Reprendre votre brouillon" in response.content.decode()
