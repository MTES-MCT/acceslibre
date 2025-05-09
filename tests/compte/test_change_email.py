from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.core import management
from django.test import Client
from django.urls import reverse

from compte.models import EmailToken
from compte.service import create_token, validate_from_token
from tests.factories import UserFactory


def client():
    return Client()


@pytest.mark.django_db
def test_create_token_function(db):
    user = UserFactory()
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    token = create_token(user, "newemail@gmail.com", activation_token, today=today)
    email_token = EmailToken.objects.get(activation_token=activation_token)

    assert token == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert str(email_token.activation_token) == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert today + timedelta(settings.EMAIL_ACTIVATION_DAYS) == email_token.expire_at


@pytest.mark.django_db
def test_user_change_email_e2e(mocker, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    user = UserFactory(username="niko")
    client.force_login(user)
    response = client.get(reverse("my_profile"))
    assert response.status_code == 200

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token_query = EmailToken.objects.all()
    assert len(email_token_query) == 1
    activation_token = email_token_query.first().activation_token
    assert activation_token is not None

    assert mock_mail.call_count == 1

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == (["test@test.com"],)
    assert _kwargs == {
        "template": "email_change_activation",
        "context": {
            "username": "niko",
            "url_change_email": f"/compte/email/change/{activation_token}/",
        },
    }


@pytest.mark.django_db
def test_user_validate_email_change(db):
    niko = UserFactory()
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    create_token(niko, "newemail@gmail.com", activation_token, today=today)

    user, failure = validate_from_token(activation_token=activation_token, today=today)

    assert user == niko
    assert failure is None
    assert len(EmailToken.objects.all()) == 0


@pytest.mark.django_db
def test_user_validate_email_expired_token(db):
    niko = UserFactory()
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    past = datetime.now(timezone.utc)
    future = datetime.now(timezone.utc) + timedelta(days=7)
    create_token(niko, "newemail@gmail.com", activation_token, today=past)

    user, failure = validate_from_token(activation_token=activation_token, today=future)

    assert user == niko
    assert failure == "Token expiré"


@pytest.mark.django_db
def test_user_validate_email_no_token(db):
    user = UserFactory()
    activation_token = None
    today = datetime.now(timezone.utc)
    create_token(user, "newemail@gmail.com", activation_token, today=today)

    user, failure = validate_from_token(activation_token=activation_token, today=today)

    assert user is None
    assert failure == "Token invalide"


@pytest.mark.django_db
def test_user_validate_email_change_e2e(db, client):
    user = UserFactory()
    client.force_login(user)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token = EmailToken.objects.all().first()
    response = client.get(
        reverse("change_email", kwargs={"activation_token": email_token.activation_token}),
        follow=True,
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert "Mon profil et préférences" in response.content.decode()
    assert len(EmailToken.objects.all()) == 0
    assert user.email == new_email


@pytest.mark.django_db
def test_user_validate_email_change_not_logged_in_e2e(db, client):
    user = UserFactory()
    client.force_login(user)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token = EmailToken.objects.all().first()

    client.logout()
    response = client.get(
        reverse("change_email", kwargs={"activation_token": email_token.activation_token}),
        follow=True,
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert "avec votre nouvelle adresse." in response.content.decode()
    assert reverse("login") in response.content.decode()
    assert len(EmailToken.objects.all()) == 0
    assert user.email == new_email


@pytest.mark.django_db
def test_deleting_unused_tokens():
    user = UserFactory()
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    last_week = datetime.now(timezone.utc) - timedelta(days=settings.EMAIL_ACTIVATION_DAYS + 1)
    create_token(user, "newemail@gmail.com", activation_token, today=last_week)
    email_tokens = EmailToken.objects.all()
    assert len(email_tokens) == 1

    management.call_command("purge_obsolete_objects_in_base")
    email_tokens = EmailToken.objects.all()
    assert len(email_tokens) == 0


def _change_client_email(client, new_email):
    response = client.post(
        reverse("my_profile"),
        data={"email1": new_email, "email2": new_email, "form_label": "email-change"},
        follow=True,
    )
    assert response.status_code == 200
    assert "Email d'activation envoyé" in response.content.decode()
