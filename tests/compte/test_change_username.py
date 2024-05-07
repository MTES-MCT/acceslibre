import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from sib_api_v3_sdk import UpdateContact

from tests.utils import assert_redirect


@pytest.fixture
def client():
    return Client()


def test_update_username_anonymous(client, data):
    response = client.get(reverse("mon_identifiant"), follow=True)
    assert_redirect(response, "/compte/login/")


def test_update_username_authenticated(mocker, client, data):
    client.force_login(data.niko)
    response = client.get(reverse("mon_identifiant"))

    assert response.status_code == 200

    mock_update_brevo = mocker.patch("sib_api_v3_sdk.ContactsApi.update_contact", return_value=True)
    client.post(reverse("mon_identifiant"), data={"username": "coucou"}, follow=True)

    assert response.status_code == 200

    # this raises if not found
    user = get_user_model().objects.get(id=data.niko.id, username="coucou")

    mock_update_brevo.assert_called_once_with(
        1,  # global mock on get_contact_info
        UpdateContact(
            attributes={
                "DATE_JOINED": user.date_joined.strftime("%Y-%m-%d"),
                "DATE_LAST_LOGIN": timezone.now().strftime("%Y-%m-%d"),
                "IS_ACTIVE": True,
                "NOM": user.last_name,
                "PRENOM": user.first_name,
                "ACTIVATION_KEY": "",
                "NB_ERPS": 1,
                "NB_ERPS_ADMINISTRATOR": 0,
                "NEWSLETTER_OPT_IN": False,
            }
        ),
    )
