import pytest

from datetime import datetime
from django.contrib.auth import get_user_model
from django.core import mail

from erp.jobs import check_closed_erps, purge_accounts
from erp.models import Erp, StatusCheck


User = get_user_model()


def test_check_closed_erps_job(data, capsys, mocker):
    assert StatusCheck.objects.filter(erp=data.erp).count() == 0

    mocker.patch(
        "erp.provider.sirene.get_siret_info",
        return_value={"actif": False, "closed_on": "2010-01-01"},
    )

    check_closed_erps.job(verbose=True)

    assert StatusCheck.objects.get(erp=data.erp).active is False

    # test email notification sent
    assert len(mail.outbox) == 1
    assert "Rapport" in mail.outbox[0].subject
    assert data.erp.nom in mail.outbox[0].body
    assert data.erp.activite.nom in mail.outbox[0].body
    assert data.erp.siret in mail.outbox[0].body
    assert data.erp.get_admin_url() in mail.outbox[0].body


def test_check_no_closed_erps_job(data, capsys, mocker):
    assert StatusCheck.objects.filter(erp=data.erp).count() == 0

    mocker.patch("erp.provider.sirene.get_siret_info", return_value={"actif": True})

    check_closed_erps.job(verbose=True)

    assert len(mail.outbox) == 0


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
