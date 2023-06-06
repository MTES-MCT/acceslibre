from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

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
