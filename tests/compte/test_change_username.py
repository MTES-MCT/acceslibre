import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from tests.utils import assert_redirect


@pytest.fixture
def client():
    return Client()


def test_update_username_anonymous(client, data):
    response = client.get(reverse("mon_identifiant"), follow=True)
    assert_redirect(response, "/compte/login/")


def test_update_username_authenticated(client, data):
    client.force_login(data.niko)
    response = client.get(reverse("mon_identifiant"))

    assert response.status_code == 200

    client.post(reverse("mon_identifiant"), data={"username": "coucou"}, follow=True)

    assert response.status_code == 200

    # this raises if not found
    get_user_model().objects.get(id=data.niko.id, username="coucou")
