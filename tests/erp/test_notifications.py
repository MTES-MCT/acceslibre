from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from requests import Response

from erp.management.commands.notify_weekly_unpublished_erps import Command
from erp.models import Accessibilite, Erp
from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory, UserFactory


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def unpublished_erp() -> Erp:
    commune = CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
    boulangerie = ActiviteFactory(nom="Boulangerie")
    erp = Erp.objects.create(
        nom="Croissants chauds",
        activite=boulangerie,
        geom=Point(6.09523, 46.27591, srid=4326),
        published=False,
        commune=commune,
        user=UserFactory(),
    )

    Accessibilite.objects.create(erp=erp, commentaire="simple commentaire")
    return erp


@pytest.fixture
def published_erp() -> Erp:
    user = UserFactory()
    activite = ActiviteFactory(nom="Boulangerie")
    erp = ErpFactory(user=user, nom="Aux bons croissants", commune="Jacou", activite=activite)
    return erp


@pytest.mark.django_db
def test_get_notification_on7days(mocker, published_erp, unpublished_erp):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
    notifs = Command(now=futur).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert notifs[0]["user"] == unpublished_erp.user
    assert notifs[0]["erps"] == [
        {
            "commune": "Jacou (34)",
            "activite": "Boulangerie",
            "slug": "croissants-chauds",
            "nom": "Croissants chauds",
            "url_publication": "/contrib/publication/croissants-chauds/",
        }
    ]


@pytest.mark.django_db
def test_get_notification_before7days(unpublished_erp):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS - 1)
    notifs = Command(now=futur).get_notifications()

    assert len(notifs) == 0


@pytest.mark.django_db
def test_get_notification_after7days(published_erp, unpublished_erp):
    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS + 3)
    notifs = Command(now=futur).get_notifications()

    assert len(Erp.objects.all()) == 2
    assert len(notifs) == 1
    assert notifs[0]["user"] == unpublished_erp.user
    assert notifs[0]["erps"] == [
        {
            "commune": "Jacou (34)",
            "activite": "Boulangerie",
            "slug": "croissants-chauds",
            "nom": "Croissants chauds",
            "url_publication": "/contrib/publication/croissants-chauds/",
        }
    ]


@pytest.mark.django_db
@override_settings(REAL_USER_NOTIFICATION=True)
def test_notification_unpublished_erp_command(mocker, unpublished_erp):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")

    futur = timezone.now() + timedelta(days=settings.UNPUBLISHED_ERP_NOTIF_DAYS)
    notify_weekly_unpublished_erps = Command(now=futur)

    call_command(notify_weekly_unpublished_erps)
    mock_mail.assert_called_once_with(
        context={
            "erps": [
                {
                    "activite": "Boulangerie",
                    "commune": "Jacou (34)",
                    "nom": "Croissants chauds",
                    "slug": "croissants-chauds",
                    "url_publication": "/contrib/publication/croissants-chauds/",
                }
            ],
            "url_mes_erps_draft": "/compte/erps/?published=0",
            "url_mes_preferences": "/compte/mon-profil/",
            "username": unpublished_erp.user.username,
        },
        template="notif_weekly_unpublished",
        to_list=[unpublished_erp.user.email],
    )


@pytest.mark.django_db
def test_notifications_default_settings():
    assert UserFactory().preferences.get().notify_on_unpublished_erps is True


@pytest.mark.django_db
def test_notifications_edit_settings(mocker, client):
    brevo_mock = mocker.patch("core.mailer.BrevoMailer.sync_user", return_value=True)

    user = UserFactory()
    client.force_login(user)
    response: Response = client.post(
        reverse("my_profile"),
        {"notify_on_unpublished_erps": False, "form_label": "preferences"},
        follow=True,
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.preferences.get().notify_on_unpublished_erps is False

    assert brevo_mock.called
