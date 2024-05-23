import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_annuaire_home(client):
    assert client.get(reverse("annuaire_home")).status_code == 200


@pytest.mark.django_db
def test_annuaire_departement(client):
    assert client.get(reverse("annuaire_departement", kwargs={"departement": "34"})).status_code == 200


@pytest.mark.django_db
def test_annuaire_departement_missing(client):
    assert client.get(reverse("annuaire_departement", kwargs={"departement": "99999"})).status_code == 404
