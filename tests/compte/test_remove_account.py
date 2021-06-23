import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.test import Client
from django.urls import reverse

from compte.service import remove_personal_informations


@pytest.fixture
def client():
    return Client()


def test_remove_account_unit(client, data):
    client.force_login(data.niko)
    uuid = "vytxeTZskVKR7C7WgdSP3d"

    response = remove_personal_informations(data.niko, lambda: uuid)

    assert response is True
    assert_user_deleted(data.niko, uuid)


def test_remove_account_e2e(client, data):
    client.force_login(data.niko)

    response = client.post(
        reverse("delete_account"),
        data={"confirm": True},
        follow=True,
    )

    assert response.status_code == 200
    assert response.wsgi_request.user.username == ""
    user_deleted = (
        get_user_model().objects.filter(username__istartswith="deleted-").first()
    )
    assert_user_deleted(user_deleted, None)


def test_remove_account_no_confirm_e2e(client, data):
    client.force_login(data.niko)

    response = client.post(
        reverse("delete_account"),
        data={"confirm": False},
        follow=True,
    )

    assert response.status_code == 200
    assert response.wsgi_request.user == data.niko


def test_erp_shows_delete_username_instead():
    pass


def assert_user_deleted(user, uuid):
    user.refresh_from_db()
    if uuid:
        assert user.username == "deleted-" + uuid
        assert check_password(uuid, user.password)
    assert user.email == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert user.is_staff is False
    assert user.is_active is False
    assert user.is_superuser is False
