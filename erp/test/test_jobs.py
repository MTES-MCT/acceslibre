import pytest

from django.core import mail

from .fixtures import data

from ..jobs import check_closed_erps
from ..models import Erp, StatusCheck


def test_check_closed_erps_job(data, capsys, mocker):
    assert StatusCheck.objects.filter(erp=data.erp).count() == 0

    mocker.patch("erp.sirene.get_siret_info", return_value={"actif": False})

    check_closed_erps.job(verbose=True)

    assert StatusCheck.objects.get(erp=data.erp).active is False

    # test email notification sent
    assert len(mail.outbox) == 1
    assert "Établissement fermé : Aux bons croissants à Jacou" in mail.outbox[0].subject
    assert data.erp.get_absolute_url() in mail.outbox[0].body
