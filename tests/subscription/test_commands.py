import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import mail
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from reversion.models import Version

from erp.models import Accessibilite, Erp
from subscription.models import ErpSubscription


@pytest.fixture
def client():
    return Client()


def niko_create_erp_and_subscribe_updates(client, data):
    "TODO: make this a reusable test helper"
    # auth user
    client.force_login(data.niko)
    # create erp admin data
    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "niko erp",
            "activite": data.boulangerie.pk,
            "numero": "4",
            "voie": "Grand rue",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "http://google.com/",
            "lat": 43.657028,
            "lon": 2.6754,
        },
        follow=True,
    )
    assert response.status_code == 200
    assert response.context["form"].errors == {}
    erp = Erp.objects.get(nom="niko erp")
    # add some a11y data
    response = client.post(
        reverse("contrib_accueil", kwargs={"erp_slug": erp.slug}),
        data={
            "sanitaires_presence": "True",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert response.context["form"].errors == {}
    erp = Erp.objects.get(nom="niko erp")
    # publish erp
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={
            "user_type": Erp.USER_ROLE_PUBLIC,
            "published": "on",
            "certif": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    # ensure erp is published
    erp = Erp.objects.get(nom="niko erp")
    assert erp.is_online() is True
    # subscribe user
    ErpSubscription.subscribe(erp, data.niko)
    return erp


def test_notification_erp(client, data, mocker):
    geo_data = {
        "numero": "4",
        "voie": "Grand rue",
        "lieu_dit": "",
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "38140",
    }
    mocker.patch("erp.provider.geocoder.query", return_value={})
    mocker.patch("erp.provider.geocoder.geocode", return_value=geo_data | {"geom": Point(0, 0)})
    erp = niko_create_erp_and_subscribe_updates(client, data)

    # sophie updates this erp data
    client.force_login(data.sophie)
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
        data=geo_data
        | {
            "source": "sirene",
            "source_id": "xxx",
            "nom": "sophie erp",
            "activite": data.boulangerie.pk,
            "site_internet": "http://google.com/",
            "action": "contribute",
            "lat": 43.657028,
            "lon": 2.6754,
        },
        follow=True,
    )

    assert response.status_code == 200
    updated_erp = Erp.objects.get(slug=erp.slug)
    assert response.context["form"].errors == {}
    assert updated_erp.nom == "sophie erp"
    assert Version.objects.count() != 0

    call_command("notify_changed_erps")
    unsubscribe_url = reverse("unsubscribe_erp", kwargs={"erp_slug": erp.slug})

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [data.niko.email]
    assert "Vous avez reçu de nouvelles contributions" in mail.outbox[0].subject
    assert "sophie erp" in mail.outbox[0].body
    assert "34830 Jacou" in mail.outbox[0].body
    assert "sophie a mis à jour les informations suivantes" in mail.outbox[0].body
    assert 'nom: "niko erp" devient "sophie erp"' in mail.outbox[0].body
    assert f"{settings.SITE_ROOT_URL}{unsubscribe_url}" in mail.outbox[0].body
    assert updated_erp.get_absolute_url() in mail.outbox[0].body


def test_notification_accessibilite(client, data, mocker):
    erp = niko_create_erp_and_subscribe_updates(client, data)

    # sophie updates this erp accessibilite data
    client.force_login(data.sophie)

    response = client.post(
        reverse("contrib_accueil", kwargs={"erp_slug": erp.slug}),
        data={
            "sanitaires_presence": "False",
            "action": "contribute",
        },
        follow=True,
    )

    assert response.status_code == 200
    updated_acc = Accessibilite.objects.get(erp__slug=erp.slug)
    assert Version.objects.exists()

    call_command("notify_changed_erps")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [data.niko.email]
    assert "Vous avez reçu de nouvelles contributions" in mail.outbox[0].subject
    assert "niko erp" in mail.outbox[0].body
    assert "34830 Jacou".lower() in mail.outbox[0].body.lower()
    assert "sophie a mis à jour les informations suivantes" in mail.outbox[0].body
    assert 'Sanitaires: "Oui" devient "Non"' in mail.outbox[0].body
    assert updated_acc.erp.get_absolute_url() in mail.outbox[0].body


def test_notification_skip_owner(client, data):
    client.force_login(data.niko)
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test update",
            "activite": data.boulangerie.pk,
            "numero": "12",
            "voie": "GRAND RUE",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "JACOU",
            "site_internet": "http://google.com/",
            "action": "contribute",
            "lat": 43.657028,
            "lon": 2.6754,
        },
        follow=True,
    )

    assert response.status_code == 200

    # niko is owner and shouldn't be notified
    call_command("notify_changed_erps")

    assert len(mail.outbox) == 0


def test_erp_publication_subscription_option(data, client):
    client.force_login(data.niko)

    # user subscribes to updates
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": data.erp.slug}),
        data={
            "user_type": Erp.USER_ROLE_PUBLIC,
            "published": "on",
            "certif": "on",
            "subscribe": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert ErpSubscription.objects.filter(erp=data.erp, user=data.niko).count() == 1

    # user unsubscribes from updates
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": data.erp.slug}),
        data={
            "user_type": Erp.USER_ROLE_PUBLIC,
            "published": "on",
            "certif": "on",
            "subscribe": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert ErpSubscription.objects.filter(erp=data.erp, user=data.niko).count() == 1
