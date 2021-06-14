from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.core import mail, management

from django.test import Client
from django.urls import reverse

from compte.models import EmailToken
from compte.service import create_token, validate_from_token


def client():
    return Client()


def test_create_token_function(db, data):
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    token = create_token(data.niko, "newemail@gmail.com", activation_token, today=today)
    email_token = EmailToken.objects.get(activation_token=activation_token)

    assert token == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert str(email_token.activation_token) == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert today + timedelta(settings.EMAIL_ACTIVATION_DAYS) == email_token.expire_at


def test_user_change_email_e2e(client, data):
    _login_client(client, data)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token_query = EmailToken.objects.all()
    assert len(email_token_query) == 1
    assert email_token_query.first().activation_token is not None

    # test email notification sent
    assert len(mail.outbox) == 1
    assert "Activation de votre compte" in mail.outbox[0].subject
    assert new_email in mail.outbox[0].recipients()
    assert "Vous avez demandé à changer votre email" in mail.outbox[0].body


def test_user_validate_email_change(db, data):
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    create_token(data.niko, "newemail@gmail.com", activation_token, today=today)

    user, failure = validate_from_token(activation_token=activation_token, today=today)

    assert failure is None
    assert len(EmailToken.objects.all()) == 0


def test_user_validate_email_expired_token(db, data):
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    past = datetime.now(timezone.utc)
    future = datetime.now(timezone.utc) + timedelta(days=7)
    create_token(data.niko, "newemail@gmail.com", activation_token, today=past)

    user, failure = validate_from_token(activation_token=activation_token, today=future)

    assert failure == "Token expiré"


def test_user_validate_email_no_token(db, data):
    activation_token = None
    today = datetime.now(timezone.utc)
    create_token(data.niko, "newemail@gmail.com", activation_token, today=today)

    user, failure = validate_from_token(activation_token=activation_token, today=today)

    assert failure == "Token invalide"


def test_user_validate_email_change_e2e(db, client, data):
    client.force_login(data.niko)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token = EmailToken.objects.all().first()
    response = client.get(
        reverse(
            "change_email", kwargs={"activation_token": email_token.activation_token}
        ),
        follow=True,
    )

    data.niko.refresh_from_db()
    assert response.status_code == 200
    assert b"Mon compte" in response.getvalue()
    assert len(EmailToken.objects.all()) == 0
    assert data.niko.email == new_email


def test_user_validate_email_change_not_logged_in_e2e(db, client, data):
    client.force_login(data.niko)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token = EmailToken.objects.all().first()

    client.logout()
    response = client.get(
        reverse(
            "change_email", kwargs={"activation_token": email_token.activation_token}
        ),
        follow=True,
    )

    data.niko.refresh_from_db()
    assert response.status_code == 200
    assert b"avec votre nouvelle adresse." in response.content
    assert reverse("login") in response.content.decode()
    assert len(EmailToken.objects.all()) == 0
    assert data.niko.email == new_email


def test_deleting_unused_tokens(data):
    activation_token = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    last_week = datetime.now(timezone.utc) - timedelta(
        days=settings.EMAIL_ACTIVATION_DAYS + 1
    )
    create_token(data.niko, "newemail@gmail.com", activation_token, today=last_week)
    email_tokens = EmailToken.objects.all()
    assert len(email_tokens) == 1

    management.call_command("purge_tokens")
    email_tokens = EmailToken.objects.all()
    assert len(email_tokens) == 0


def _change_client_email(client, new_email):
    response = client.post(
        reverse("mon_email"),
        data={"email1": new_email, "email2": new_email},
        follow=True,
    )
    assert response.status_code == 200


def _login_client(client, data):
    client.force_login(data.niko)
    response = client.get(reverse("mon_identifiant"))
    assert response.status_code == 200
