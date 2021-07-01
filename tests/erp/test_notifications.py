from datetime import datetime, timezone, timedelta

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import mail
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from requests import Response

from erp.models import Erp, Accessibilite, Activite
from erp.management.commands.notify_unpublished_erps import Command


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def activite_boulangerie(db) -> Activite:
    return Activite.objects.create(nom="Boulangerie")


@pytest.fixture
def unpublished_erp(data) -> Erp:
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


def test_get_notification_on7days(unpublished_erp, data):
    futur = datetime.now(timezone.utc) + timedelta(days=7)
    notifs = Command(now=futur).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert (notifs[0].user, notifs[0]) == (data.niko, unpublished_erp)


def test_get_notification_before7days(unpublished_erp, data):
    futur = datetime.now(timezone.utc) + timedelta(days=6)
    notifs = Command(now=futur).get_notifications()

    assert len(notifs) == 0


def test_get_notification_after7days(unpublished_erp, data):
    futur = datetime.now(timezone.utc) + timedelta(days=10)
    notifs = Command(now=futur).get_notifications()

    assert len(notifs) == 0


def test_get_notification_after14days(unpublished_erp, data):
    futur = datetime.now(timezone.utc) + timedelta(days=14)
    notifs = Command(now=futur).get_notifications()

    assert len(notifs) == 1
    assert (notifs[0].user, notifs[0]) == (data.niko, unpublished_erp)


def test_notification_unpublished_erp_command(unpublished_erp, data):
    futur = datetime.now(timezone.utc) + timedelta(days=7)
    notify_unpublished_erps = Command(now=futur)
    unsubscribe_url = reverse("mes_preferences")

    call_command(notify_unpublished_erps)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [data.niko.email]
    assert "Rappel: publiez votre ERP !" in mail.outbox[0].subject
    assert "Chaque information est précieuse" in mail.outbox[0].body
    assert unpublished_erp.get_absolute_url() in mail.outbox[0].body
    assert f"{settings.SITE_ROOT_URL}{unsubscribe_url}" in mail.outbox[0].body


def test_notifications_default_settings(data):
    assert data.niko.preferences.get().notify_on_unpublished_erps is True


def test_notifications_edit_settings(client, data):
    client.force_login(data.niko)
    response: Response = client.post(
        reverse("mes_preferences"),
        {
            "notify_on_unpublished_erps": False,
        },
        follow=True,
    )

    data.niko.refresh_from_db()
    assert response.status_code == 200
    assert data.niko.preferences.get().notify_on_unpublished_erps is False
