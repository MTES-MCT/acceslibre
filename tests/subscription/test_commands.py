import pytest
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse
from reversion.models import Version

from erp.models import Erp
from subscription.models import ErpSubscription
from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory, UserFactory
from unittest.mock import ANY


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def niko_create_erp_and_subscribe_updates(client):
    niko = UserFactory(is_staff=True, email="niko@niko.tld", username="niko")
    boulangerie = ActiviteFactory(nom="boulangerie")
    sophie = UserFactory(username="sophie")
    ActiviteFactory(slug="autre")
    CommuneFactory(nom="Jacou", departement=34)

    client.force_login(niko)
    # create erp admin data
    response = client.post(
        reverse("contrib_admin_infos"),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "niko erp",
            "activite": boulangerie.nom,
            "numero": "5",
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
            "accueil_visibilite": "True",
            "accueil_audiodescription_presence": "True",
            "accueil_retrecissement": "True",
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
    assert erp.published is True
    # subscribe user
    ErpSubscription.subscribe(erp, niko)
    return erp, boulangerie, niko, sophie


@pytest.mark.django_db
@override_settings(REAL_USER_NOTIFICATION=True)
def test_notification_erp(mocker, mock_geocode, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    erp, boulangerie, niko, sophie = niko_create_erp_and_subscribe_updates(client)

    # sophie updates this erp data
    client.force_login(sophie)
    payload = {
        "source": "sirene",
        "source_id": "xxx",
        "nom": "sophie erp",
        "activite": boulangerie.nom,
        "site_internet": "http://google.com/",
        "action": "contribute",
        "numero": "4",
        "voie": "Grand rue",
        "lieu_dit": "",
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "38140",
        "lat": 45,
        "lon": 5,
    }
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
        data=payload,
        follow=True,
    )

    # second edition
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
        data=payload | {"site_internet": "https://bing.com"},
        follow=True,
    )

    assert response.status_code == 200
    updated_erp = Erp.objects.get(slug=erp.slug)
    assert response.context["form"].errors == {}
    assert updated_erp.nom == "sophie erp"
    assert Version.objects.count() != 0

    call_command("notify_changed_erps")

    assert mock_mail.call_count == 1

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == ([niko.email],)
    assert _kwargs == {
        "template": "changed_erp_notification",
        "context": {
            "username": "niko",
            "erps": [
                {
                    "code_postal": "34830",
                    "commune": "Jacou",
                    "nom": "sophie erp",
                    "get_absolute_url": "/app/34-jacou/a/boulangerie/erp/niko-erp/",
                    "changes_by_others": [
                        {
                            "user": "sophie",
                            "revision": ANY,
                            "comment": "",
                            "diff": [
                                {
                                    "field": "site_internet",
                                    "label": "site_internet",
                                    "new": "https://bing.com",
                                    "old": "http://google.com/",
                                },
                            ],
                        },
                        {
                            "user": "sophie",
                            "revision": ANY,
                            "comment": "",
                            "diff": [
                                {"field": "nom", "old": "niko erp", "new": "sophie erp", "label": "nom"},
                                {"field": "geom", "old": "43.6570, 2.6754", "new": "45.0000, 5.0000", "label": "geom"},
                                {"field": "numero", "old": "5", "new": "4", "label": "numero"},
                                {"field": "commune", "old": "JACOU", "new": "Jacou", "label": "commune"},
                            ],
                        },
                    ],
                    "url_unsubscribe": "/subscription/unsubscribe/erp/niko-erp/",
                },
            ],
            "url_changed_erp_notification": "/compte/contributions/recues/",
        },
    }


@pytest.mark.django_db
@override_settings(REAL_USER_NOTIFICATION=True)
def test_notification_accessibilite(client, mocker):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    erp, _, niko, sophie = niko_create_erp_and_subscribe_updates(client)

    # sophie updates this erp accessibilite data
    client.force_login(sophie)

    response = client.post(
        reverse("contrib_accueil", kwargs={"erp_slug": erp.slug}),
        data={
            "sanitaires_presence": "False",
            "action": "contribute",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Version.objects.exists()

    call_command("notify_changed_erps")

    assert mock_mail.call_count == 1

    _args, _kwargs = mock_mail.call_args_list[0]
    assert _args == ([niko.email],)
    assert _kwargs == {
        "template": "changed_erp_notification",
        "context": {
            "username": "niko",
            "erps": [
                {
                    "code_postal": "34830",
                    "commune": "JACOU",
                    "nom": "niko erp",
                    "get_absolute_url": "/app/34-jacou/a/boulangerie/erp/niko-erp/",
                    "changes_by_others": [
                        {
                            "user": "sophie",
                            "revision": ANY,
                            "comment": "",
                            "diff": [
                                {
                                    "field": "accueil_visibilite",
                                    "old": "Oui",
                                    "new": "Inconnu",
                                    "label": "Visibilité de la zone d'accueil",
                                },
                                {
                                    "field": "accueil_audiodescription_presence",
                                    "old": "Oui",
                                    "new": "Inconnu",
                                    "label": "Audiodescription",
                                },
                                {
                                    "field": "accueil_audiodescription",
                                    "old": "Vide",
                                    "new": "None",
                                    "label": "Type d'équipements pour l'audiodescription",
                                },
                                {
                                    "field": "accueil_retrecissement",
                                    "old": "Oui",
                                    "new": "Inconnu",
                                    "label": "Rétrécissement du chemin",
                                },
                                {"field": "sanitaires_presence", "old": "Oui", "new": "Non", "label": "Toilettes"},
                            ],
                        }
                    ],
                    "url_unsubscribe": "/subscription/unsubscribe/erp/niko-erp/",
                },
            ],
            "url_changed_erp_notification": "/compte/contributions/recues/",
        },
    }


@pytest.mark.django_db
@override_settings(REAL_USER_NOTIFICATION=True)
def test_notification_skip_owner(mocker, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    user = UserFactory()
    boulangerie = ActiviteFactory(nom="boulangerie")
    ActiviteFactory(slug="autre")
    erp = ErpFactory(user=user)

    client.force_login(user)
    response = client.post(
        reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
        data={
            "source": "sirene",
            "source_id": "xxx",
            "nom": "Test update",
            "activite": boulangerie.pk,
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

    mock_mail.assert_not_called


@pytest.mark.django_db
def test_erp_publication_subscription_option(client):
    niko = UserFactory(is_staff=True, email="niko@niko.tld", username="niko")
    CommuneFactory(nom="Jacou", departement=34)
    erp = ErpFactory(with_accessibilite=True, commune="Jacou", user=niko)

    client.force_login(niko)

    # user subscribes to updates
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={
            "user_type": Erp.USER_ROLE_PUBLIC,
            "published": "on",
            "certif": "on",
            "subscribe": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert ErpSubscription.objects.filter(erp=erp, user=niko).count() == 1

    # user unsubscribes from updates
    response = client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
        data={
            "user_type": Erp.USER_ROLE_PUBLIC,
            "published": "on",
            "certif": "on",
            "subscribe": "on",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert ErpSubscription.objects.filter(erp=erp, user=niko).count() == 1
