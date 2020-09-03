import pytest

from django.core import mail

from erp.jobs import check_closed_erps
from erp.models import Erp, StatusCheck

from tests.fixtures import data


def test_check_closed_erps_job(data, capsys, mocker):
    assert StatusCheck.objects.filter(erp=data.erp).count() == 0

    mocker.patch("erp.sirene.get_siret_info", return_value={"actif": False})

    check_closed_erps.job(verbose=True)

    assert StatusCheck.objects.get(erp=data.erp).active is False

    # test email notification sent
    assert len(mail.outbox) == 1
    assert "Rapport quotidien" in mail.outbox[0].subject
    assert "Aux bons croissants" in mail.outbox[0].body
    assert data.erp.get_absolute_url() in mail.outbox[0].body
    assert data.erp.get_admin_url() in mail.outbox[0].body


def test_check_no_closed_erps_job(data, capsys, mocker):
    assert StatusCheck.objects.filter(erp=data.erp).count() == 0

    mocker.patch("erp.sirene.get_siret_info", return_value={"actif": True})

    check_closed_erps.job(verbose=True)

    assert len(mail.outbox) == 1
    assert "Rapport quotidien" in mail.outbox[0].subject
    assert "Aucun établissement" in mail.outbox[0].body
