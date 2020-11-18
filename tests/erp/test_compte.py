import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from tests.fixtures import data
from tests.utils import assert_redirect


@pytest.fixture
def client():
    return Client()


def test_update_username_anonymous(client, data):
    response = client.get(reverse("mon_identifiant"), follow=True)
    assert_redirect(response, "/accounts/login/")


def test_update_username_authenticated(client, data):
    client.login(username="niko", password="Abc12345!")
    response = client.get(reverse("mon_identifiant"))

    assert response.status_code == 200

    client.post(reverse("mon_identifiant"), data={"username": "coucou"}, follow=True)

    assert response.status_code == 200
    assert User.objects.filter(id=data.niko.id, username="coucou").count() == 1
