from unittest.mock import ANY

from django.conf import settings
from django.core import mail
from django.urls import reverse

from contact.models import Message

TEST_NAME = "Joe Test"
TEST_EMAIL = "joe@test.com"
TEST_BODY = "This is a test"

RECEIPT_CONTENT_NORMAL = "contacter directement les gestionnaires de l'établissement"
RECEIPT_CONTENT_VACCINATION = "prise de rendez-vous de vaccination"


def test_contact(mocker, data, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

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

    assert response.status_code == 302
    assert mock_mail.call_count == 2

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == ([settings.DEFAULT_EMAIL],)
    assert _kwargs == {
        "context": {
            "message": {
                "name": TEST_NAME,
                "body": TEST_BODY,
                "username": None,
                "topic": "Signaler une malveillance",
                "email": TEST_EMAIL,
            }
        },
        "reply_to": TEST_EMAIL,
        "template": "contact_to_admins",
    }

    _args, _kwargs = mock_mail.call_args_list[1]
    assert _args == ([TEST_EMAIL],)
    assert _kwargs == {
        "context": {"message_date": ANY, "erp": ""},
        "template": "contact_receipt",
    }

    assert (
        Message.objects.filter(
            topic="signalement",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            sent_ok=True,
        ).count()
        == 1
    )


def test_contact_antispam(data, client):
    response = client.post(
        reverse("contact_form"),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
        },
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 0

    assert 0 == Message.objects.count()


def test_contact_authenticated(mocker, data, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    client.force_login(data.niko)

    response = client.get(reverse("contact_form"))
    assert response.context["form"].initial["user"] == data.niko
    assert 'value="niko@niko.tld"' in response.content.decode()

    response = client.post(
        reverse("contact_form"),
        {
            "topic": "signalement",
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "body": TEST_BODY,
            "user": str(data.erp.user.pk),
            "robot": "on",
        },
    )

    assert response.status_code == 302
    assert mock_mail.call_count == 2

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == ([settings.DEFAULT_EMAIL],)
    assert _kwargs == {
        "context": {
            "message": {
                "name": TEST_NAME,
                "body": TEST_BODY,
                "username": "niko",
                "topic": "Signaler une malveillance",
                "email": TEST_EMAIL,
            }
        },
        "reply_to": TEST_EMAIL,
        "template": "contact_to_admins",
    }

    _args, _kwargs = mock_mail.call_args_list[1]
    assert _args == ([TEST_EMAIL],)
    assert _kwargs == {
        "context": {"message_date": ANY, "erp": ""},
        "template": "contact_receipt",
    }

    assert (
        Message.objects.filter(
            topic="signalement",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            sent_ok=True,
        ).count()
        == 1
    )


def test_contact_topic(mocker, data, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    response = client.post(
        reverse("contact_topic", kwargs={"topic": "api"}),
        {
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "topic": "api",
            "body": TEST_BODY,
            "robot": "on",
        },
    )

    assert response.status_code == 302
    assert mock_mail.call_count == 2

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == ([settings.DEFAULT_EMAIL],)
    assert _kwargs == {
        "context": {
            "message": {
                "name": TEST_NAME,
                "body": TEST_BODY,
                "username": None,
                "topic": "API",
                "email": TEST_EMAIL,
            }
        },
        "reply_to": TEST_EMAIL,
        "template": "contact_to_admins",
    }

    _args, _kwargs = mock_mail.call_args_list[1]
    assert _args == ([TEST_EMAIL],)
    assert _kwargs == {
        "context": {"message_date": ANY, "erp": ""},
        "template": "contact_receipt",
    }

    assert (
        Message.objects.filter(
            topic="api",
            name=TEST_NAME,
            email=TEST_EMAIL,
            body=TEST_BODY,
            sent_ok=True,
        ).count()
        == 1
    )
