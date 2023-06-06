from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework_api_key.models import APIKey

from erp.models import Erp

User = get_user_model()


@pytest.fixture
def spambot(db):
    return User.objects.create_user(
        username="spambot",
        password="Abc12345!",
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
def test_purge_api_tokens():
    to_keep, _ = APIKey.objects.create_key(name="to_not_delete", expiry_date=datetime.now() - timedelta(hours=2))
    to_keep2, _ = APIKey.objects.create_key(
        name=settings.INTERNAL_API_KEY_NAME, expiry_date=datetime.now() + timedelta(hours=1)
    )
    to_delete, _ = APIKey.objects.create_key(
        name=settings.INTERNAL_API_KEY_NAME, expiry_date=datetime.now() - timedelta(hours=2)
    )
    call_command("purge_obsolete_objects_in_base")

    assert APIKey.objects.filter(pk__in=(to_keep.pk, to_keep2.pk)).count() == 2
    assert APIKey.objects.filter(pk=to_delete.pk).first() is None
