from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from erp.models import Erp, ExternalSource
from tests.factories import CommuneFactory, ErpFactory, UserFactory

User = get_user_model()


@pytest.fixture
def spambot(db):
    return User.objects.create_user(
        username="spambot",
        password="Abc123456789!",
        email="spam@bot.tld",
        is_staff=False,
        is_active=False,
        date_joined=datetime(2020, 1, 1),
    )


def test_purge_accounts_purge_user(spambot):
    assert User.objects.filter(username="spambot").count() == 1

    call_command("purge_obsolete_objects_in_base", today="2020-06-01")

    assert User.objects.filter(username="spambot").count() == 0


def test_purge_accounts_keep_user(spambot):
    assert User.objects.filter(username="spambot").count() == 1

    call_command("purge_obsolete_objects_in_base", today="2020-01-29")

    assert User.objects.filter(username="spambot").count() == 1


def test_purge_accounts_keep_inactive_with_erps(spambot):
    # user has been deactivated after they created erps
    assert User.objects.filter(username="spambot").count() == 1
    Erp.objects.create(nom="test", user=spambot)

    call_command("purge_obsolete_objects_in_base", today="2020-06-01")

    assert User.objects.filter(username="spambot").count() == 1


@pytest.mark.django_db
def test_sync_brevo(mocker, client):
    today = timezone.now()
    mock = mocker.patch("sib_api_v3_sdk.ContactsApi.update_contact", return_value=True)
    call_command("sync_brevo")

    assert mock.call_count == 0

    user = UserFactory(last_login=today)

    mock.reset_mock()
    call_command("sync_brevo")

    assert mock.call_count == 1
    _, _kwargs = mock.call_args_list[0][0]

    assert _kwargs.attributes == {
        "ACTIVATION_KEY": "",
        "DATE_JOINED": today.strftime("%Y-%m-%d"),
        "DATE_LAST_CONTRIB": "",
        "DATE_LAST_LOGIN": today.strftime("%Y-%m-%d"),
        "IS_ACTIVE": True,
        "NB_ERPS": 0,
        "NB_ERPS_ADMINISTRATOR": 0,
        "NEWSLETTER_OPT_IN": False,
        "NOM": user.last_name,
        "PRENOM": user.first_name,
        "AVERAGE_COMPLETION_RATE": 0,
    }

    erp = ErpFactory(with_accessibilite=True, user=None)
    CommuneFactory(nom=erp.commune)
    client.force_login(user)
    client.post(
        reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug}),
        data={
            "commentaire": "I own this establishment",
        },
        follow=True,
    )

    erp.refresh_from_db()
    assert erp.user == user, "ERP should have been attributed to editor"

    mock.reset_mock()
    call_command("sync_brevo")
    assert mock.call_count == 1
    _, _kwargs = mock.call_args_list[0][0]

    assert _kwargs.attributes == {
        "ACTIVATION_KEY": "",
        "DATE_JOINED": today.strftime("%Y-%m-%d"),
        "DATE_LAST_CONTRIB": today.strftime("%Y-%m-%d"),
        "DATE_LAST_LOGIN": today.strftime("%Y-%m-%d"),
        "IS_ACTIVE": True,
        "NB_ERPS": 1,
        "NB_ERPS_ADMINISTRATOR": 0,
        "NEWSLETTER_OPT_IN": False,
        "NOM": user.last_name,
        "PRENOM": user.first_name,
        "AVERAGE_COMPLETION_RATE": 4.0,
    }

    erp = ErpFactory(import_email=user.email, source=ExternalSource.SOURCE_TALLY)

    mock.reset_mock()
    call_command("sync_brevo")
    assert mock.call_count == 2
    _, _kwargs = mock.call_args_list[1][0]

    assert _kwargs.attributes == {
        "ERP_URL": erp.get_absolute_uri(),
    }
