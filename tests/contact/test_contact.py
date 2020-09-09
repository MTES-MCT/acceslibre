import pytest

from datetime import date

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client
from django.urls import reverse

from erp.models import Erp
from contact.models import Message

from tests.fixtures import data

TEST_NAME = "Joe Test"
TEST_EMAIL = "joe@test.com"
TEST_BODY = "This is a test"


def test_contact(data, client):
    response = client.post(
        reverse("contact_form"),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
        },
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "[signalement]" in mail.outbox[0].subject
    assert TEST_NAME in mail.outbox[0].body
    assert TEST_EMAIL in mail.outbox[0].body
    assert TEST_BODY in mail.outbox[0].body

    assert (
        1
        == Message.objects.filter(
            topic="signalement",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            sent_ok=True,
        ).count()
    )


def test_contact_antispam(data, client):
    response = client.post(
        reverse("contact_form"),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
            "robot": "on",
        },
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 0

    assert 0 == Message.objects.count()


def test_contact_authenticated(data, client):
    response = client.post(
        reverse("contact_form"),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
            "user": str(data.erp.user.pk),
        },
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "[signalement]" in mail.outbox[0].subject
    assert data.erp.user.username in mail.outbox[0].body
    assert TEST_BODY in mail.outbox[0].body

    assert (
        1
        == Message.objects.filter(
            topic="signalement", user=data.erp.user, body=TEST_BODY, sent_ok=True,
        ).count()
    )


def test_contact_topic(data, client):
    response = client.post(
        reverse("contact_topic", kwargs={"topic": "a11y"}),
        {"name": TEST_NAME, "email": TEST_EMAIL, "topic": "a11y", "body": TEST_BODY,},
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "[a11y]" in mail.outbox[0].subject
    assert TEST_NAME in mail.outbox[0].body
    assert TEST_EMAIL in mail.outbox[0].body
    assert TEST_BODY in mail.outbox[0].body

    assert (
        1
        == Message.objects.filter(
            topic="a11y",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            sent_ok=True,
        ).count()
    )


def test_contact_topic_erp(data, client):
    response = client.post(
        reverse(
            "contact_topic_erp",
            kwargs={"topic": "signalement", "erp_slug": data.erp.slug},
        ),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
            "erp": str(data.erp.pk),
        },
    )

    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "[signalement]" in mail.outbox[0].subject
    assert TEST_NAME in mail.outbox[0].body
    assert TEST_EMAIL in mail.outbox[0].body
    assert TEST_BODY in mail.outbox[0].body
    assert data.erp.nom in mail.outbox[0].body

    assert (
        1
        == Message.objects.filter(
            topic="signalement",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            erp=data.erp,
            sent_ok=True,
        ).count()
    )
