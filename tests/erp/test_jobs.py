import pytest

from datetime import datetime
from django.contrib.auth import get_user_model
from django.core import mail

from erp.jobs import purge_accounts
from erp.models import Erp


User = get_user_model()


# purge_accounts.py


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


def test_purge_accounts_job_purge_user(spambot):
    assert User.objects.filter(username="spambot").count() == 1

    purge_accounts.job(today=datetime(2020, 6, 1))

    assert User.objects.filter(username="spambot").count() == 0


def test_purge_accounts_job_keep_user(spambot):
    assert User.objects.filter(username="spambot").count() == 1

    purge_accounts.job(today=datetime(2020, 1, 29))

    assert User.objects.filter(username="spambot").count() == 1


def test_purge_accounts_job_keep_inactive_with_erps(spambot):
    # user has been deactivated after they created erps
    assert User.objects.filter(username="spambot").count() == 1
    Erp.objects.create(nom="test", user=spambot)

    purge_accounts.job(today=datetime(2020, 6, 1))

    assert User.objects.filter(username="spambot").count() == 1
