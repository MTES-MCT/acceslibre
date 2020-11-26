import pytest

from django.core import mail

from erp.jobs import check_closed_erps
from erp.models import Erp, StatusCheck

from tests.fixtures import data


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
