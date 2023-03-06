from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import mail
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from requests import Response

from erp.management.commands.notify_unpublished_erps import Command
from erp.models import Accessibilite, Erp


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def unpublished_erp(data) -> Erp:
    erp = Erp.objects.create(
        nom="Croissants chauds",
        activite=data.boulangerie,
        geom=Point(6.09523, 46.27591, srid=4326),
        published=False,
        commune=data.jacou,
        user=data.niko,
    )

    Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
    return erp


def test_get_notification_on7days(unpublished_erp, data):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
    notifs = Command(now=futur).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert notifs[0]["user"] == data.niko
    assert notifs[0]["erps"] == [unpublished_erp]


def test_get_notification_before7days(unpublished_erp, data):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS - 1)
    notifs = Command(now=futur).get_notifications()

    assert len(notifs) == 0


def test_get_notification_after7days(unpublished_erp, data):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS + 3)
    notifs = Command(now=futur).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert notifs[0]["user"] == data.niko
    assert notifs[0]["erps"] == [unpublished_erp]


@override_settings(REAL_USER_NOTIFICATION=True)
def test_notification_unpublished_erp_command(unpublished_erp, data):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
    notify_unpublished_erps = Command(now=futur)

    call_command(notify_unpublished_erps)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [data.niko.email]
    assert "Des établissements sont en attente de publication" in mail.outbox[0].subject
    assert "Boulangerie: Croissants chauds, Jacou (34)" in mail.outbox[0].body
    assert reverse("mes_preferences") in mail.outbox[0].body
    assert reverse("contrib_publication", kwargs={"erp_slug": unpublished_erp.slug}) in mail.outbox[0].body


def test_notifications_default_settings(data):
    assert data.niko.preferences.get().notify_on_unpublished_erps is True


def test_notifications_edit_settings(client, data):
    client.force_login(data.niko)
    response: Response = client.post(
        reverse("mes_preferences"),
        {"notify_on_unpublished_erps": False},
        follow=True,
    )

    data.niko.refresh_from_db()
    assert response.status_code == 200
    assert data.niko.preferences.get().notify_on_unpublished_erps is False
