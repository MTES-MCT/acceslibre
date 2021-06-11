from datetime import datetime, timedelta, timezone

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail

from django.test import Client
from django.urls import reverse
from django.utils.timezone import make_naive

from auth.models import EmailToken
from auth.service import create_token, validate_from_token


def client():
    return Client()


def test_create_token_function(db, data):
    uuid = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    token = create_token(data.niko, "newemail@gmail.com", uuid, today=today)
    email_token = EmailToken.objects.get(token=token)

    assert token == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert str(email_token.token) == "a603ae0a-4188-4098-99ca-3b853642c1c7"
    assert today + timedelta(settings.EMAIL_ACTIVATION_DAYS) == email_token.expire_at


def test_user_change_email_e2e(client, data):
    _login_client(client, data)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token_query = EmailToken.objects.all()
    assert len(email_token_query) == 1
    assert email_token_query.first().token is not None

    # test email notification sent
    assert len(mail.outbox) == 1
    assert "Activation de votre compte" in mail.outbox[0].subject
    assert new_email in mail.outbox[0].recipients()
    assert "Vous avez demandé à changer votre email" in mail.outbox[0].body


def test_user_validate_email_change(db, data):
    uuid = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    today = datetime.now(timezone.utc)
    create_token(data.niko, "newemail@gmail.com", uuid, today=today)

    failure = validate_from_token(data.niko, activation_key=uuid, today=today)

    assert failure is None
    assert len(EmailToken.objects.all()) == 0


def test_user_validate_email_expired_token(db, data):
    uuid = "a603ae0a-4188-4098-99ca-3b853642c1c7"
    past = datetime.now(timezone.utc)
    future = datetime.now(timezone.utc) + timedelta(days=7)
    create_token(data.niko, "newemail@gmail.com", uuid, today=past)

    failure = validate_from_token(data.niko, activation_key=uuid, today=future)

    assert failure == "Token expiré"


def test_user_validate_email_no_token(db, data):
    uuid = None
    today = datetime.now(timezone.utc)
    create_token(data.niko, "newemail@gmail.com", uuid, today=today)

    failure = validate_from_token(data.niko, activation_key=uuid, today=today)

    assert failure == "Token invalide"


def test_user_validate_email_change_e2e(db, client, data):
    client.force_login(data.niko)

    new_email = "test@test.com"
    _change_client_email(client, new_email)

    email_token = EmailToken.objects.all().first()
    response = client.get(
        reverse("change_email", kwargs={"activation_key": email_token.token}),
        follow=True,
    )

    data.niko.refresh_from_db()
    assert response.status_code == 200
    assert len(EmailToken.objects.all()) == 0
    assert data.niko.email == new_email


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
