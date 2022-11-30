import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


def test_annuaire_home(data, client):
    assert client.get(reverse("annuaire_home")).status_code == 200


def test_annuaire_departement(data, client):
    assert (
        client.get(
            reverse("annuaire_departement", kwargs={"departement": "34"})
        ).status_code
        == 200
    )


def test_annuaire_departement_missing(data, client):
    assert (
        client.get(
            reverse("annuaire_departement", kwargs={"departement": "99999"})
        ).status_code
        == 404
    )
