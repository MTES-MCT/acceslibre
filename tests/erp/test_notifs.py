import pytest

from django.core import mail
from django.test import Client
from django.urls import reverse

from erp.models import Accessibilite, Erp
from erp.jobs import notify_changed_erps

from tests.fixtures import data

from reversion.models import Version


@pytest.fixture
def client():
    return Client()


def test_notification_erp(client, data):
    client.login(username="sophie", password="Abc12345!")
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test contribution",
            "recevant_du_public": True,
            "activite": data.boulangerie.pk,
            "siret": "21690266800013",
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "http://google.com/",
            "action": "contribute",
        },
        follow=True,
    )

    assert response.status_code == 200
    updated_erp = Erp.objects.get(slug=data.erp.slug)
    assert response.context["form"].errors == {}
    assert updated_erp.nom == "Test contribution"
    assert Version.objects.count() != 0

    notify_changed_erps.job()

    assert len(mail.outbox) == 1
    assert "Vous avez reçu de nouvelles contributions" in mail.outbox[0].subject
    assert "- sophie sur Test contribution (Jacou)" in mail.outbox[0].body
    assert updated_erp.get_absolute_url() in mail.outbox[0].body


def test_notification_accessibilite(client, data):
    client.login(username="sophie", password="Abc12345!")
    response = client.post(
        reverse("contrib_sanitaires", kwargs={"erp_slug": data.erp.slug}),
        data={
            "sanitaires_presence": "True",
            "sanitaires_adaptes": "1",
            "action": "contribute",
        },
        follow=True,
    )

    assert response.status_code == 200
    updated_acc = Accessibilite.objects.get(erp__slug=data.erp.slug)
    assert Version.objects.count() != 0

    notify_changed_erps.job()

    assert len(mail.outbox) == 1
    assert "Vous avez reçu de nouvelles contributions" in mail.outbox[0].subject
    assert "- sophie sur Aux bons croissants (Jacou)" in mail.outbox[0].body
    assert updated_acc.erp.get_absolute_url() in mail.outbox[0].body


def test_notification_skip_owner(client, data):
    client.login(username="niko", password="Abc12345!")
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test update",
            "recevant_du_public": True,
            "activite": data.boulangerie.pk,
            "siret": "21690266800013",
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "http://google.com/",
            "action": "contribute",
        },
        follow=True,
    )

    assert response.status_code == 200

    # niko is owner and shouldn't be notified
    notify_changed_erps.job()

    assert len(mail.outbox) == 0
