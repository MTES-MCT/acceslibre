from datetime import datetime

import pytest
from django.contrib.auth import get_user_model

from django.test import Client
from django.urls import reverse

from auth.service import create_token


def client():
    return Client()


@pytest.mark.integration
def test_create_token(db, data):
    uuid = "test_uuid"
    today = datetime.utcnow()
    token = create_token(data.niko, "newemail@gmail.com", uuid, today=today)

    assert token == "test_uuid"


@pytest.mark.integration
def test_user_change_email(client, data):
    client.force_login(data.niko)
    response = client.get(reverse("mon_identifiant"))

    assert response.status_code == 200

    client.post(reverse("mon_identifiant"), data={"username": "coucou"}, follow=True)

    assert response.status_code == 200

    # this raises if not found
    get_user_model().objects.get(id=data.niko.id, username="coucou")
    pass


@pytest.mark.integration
def test_user_validate_email_change():
    pass
