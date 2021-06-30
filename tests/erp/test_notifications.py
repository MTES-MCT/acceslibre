from datetime import datetime, timezone, timedelta

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import mail
from django.core.management import call_command
from django.urls import reverse

from erp.models import Erp, Accessibilite, Activite
from erp.management.commands.notify_unpublished_erps import Command


@pytest.fixture
def activite_boulangerie(db):
    return Activite.objects.create(nom="Boulangerie")


@pytest.fixture
def unpublished_erp(data):
    erp = Erp.objects.create(
        nom="Boulangerie",
        activite=data.boulangerie,
        geom=Point(6.09523, 46.27591),
        published=False,
        commune=data.jacou,
        user=data.niko,
    )

    Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
    return erp


def test_get_notification(unpublished_erp, data):
    past = datetime.now(timezone.utc) - timedelta(days=10)
    notifs = Command(now=past).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert (notifs[0][0], notifs[0][1]) == (data.niko, unpublished_erp)


def test_notification_unpublished_erp_command(unpublished_erp, data):
    past = datetime.now(timezone.utc) - timedelta(days=10)
    notify_unpublished_erps = Command(now=past)
    unsubscribe_url = reverse("disable_reminders")

    call_command(notify_unpublished_erps)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [data.niko.email]
    assert "Rappel: publiez votre ERP !" in mail.outbox[0].subject
    assert "Chaque information est précieuse" in mail.outbox[0].body
    assert unpublished_erp.get_absolute_url() in mail.outbox[0].body
    assert f"{settings.SITE_ROOT_URL}{unsubscribe_url}" in mail.outbox[0].body
