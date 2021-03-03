import pytest

from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


def test_annuaire(data, client):
    assert client.get(reverse("annuaire_home")).status_code == 200
    assert (
        client.get(
            reverse("annuaire_departement", kwargs={"departement": "34"})
        ).status_code
        == 200
    )
