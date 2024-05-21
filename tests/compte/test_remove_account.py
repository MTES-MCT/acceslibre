import pytest
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse

from compte import service
from tests.factories import UserFactory


@pytest.fixture
def pseudo_random_string(mocker):
    pseudo_random_string = "vytxeTZskVKR7C7WgdSP"
    mocker.patch("core.lib.text.random_string", return_value=pseudo_random_string)
    return pseudo_random_string


@pytest.mark.django_db
def test_delete_account_anonymize_user(data, pseudo_random_string):
    user = UserFactory(is_staff=True, is_active=True)
    anonymized_user = service.anonymize_user(user)

    assert anonymized_user.pk == user.pk
    assert_user_anonymized(user, pseudo_random_string)


@pytest.mark.django_db
def test_delete_account_e2e(client, pseudo_random_string):
    user = UserFactory(is_staff=True, is_active=True, username="niko")
    client.force_login(user)

    response = client.post(
        reverse("delete_account"),
        data={"confirm": True},
        follow=True,
    )

    assert response.status_code == 200
    assert response.wsgi_request.user.username == ""

    anonymized_user = get_user_model().objects.get(
        pk=user.pk,
        username__startswith=service.DELETED_ACCOUNT_USERNAME,
    )
    assert_user_anonymized(anonymized_user, pseudo_random_string)

    assert (
        LogEntry.objects.filter(
            object_repr="niko",
            change_message='Compte "niko" désactivé et anonymisé',
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_delete_account_no_confirm_e2e(client, data):
    user = UserFactory(is_staff=True, is_active=True)
    client.force_login(user)

    response = client.post(
        reverse("delete_account"),
        data={"confirm": False},
        follow=True,
    )

    assert response.status_code == 200
    assert "confirm" in response.context["form"].errors
    assert response.wsgi_request.user == user


def assert_user_anonymized(user, random_string):
    user.refresh_from_db()
    assert user.username.startswith(service.DELETED_ACCOUNT_USERNAME)
    assert check_password(random_string, user.password)
    assert user.email == ""
    assert user.last_name == ""
    assert user.is_staff is False
    assert user.is_active is False
    assert user.is_superuser is False
