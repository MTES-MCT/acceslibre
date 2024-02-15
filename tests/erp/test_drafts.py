import uuid
from copy import deepcopy

import pytest
from django.test import Client
from django.urls import reverse

from erp.models import Erp


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_result(data):
    return {
        "exists": data.erp,
        "source": "entreprise_api",
        "source_id": "63015890",
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
        "activite": None,
        "nom": "Akei",
        "siret": "88076068100010",
        "numero": "4",
        "voie": "Grand Rue",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "34120",
        "contact_email": None,
        "telephone": None,
        "site_internet": None,
    }


@pytest.fixture
def test_response(client, mocker, sample_result):
    def _factory(user_to_log_in):
        mocker.patch("erp.provider.search.global_search", return_value=[sample_result])
        client.force_login(user_to_log_in)
        return client.get(
            reverse("contrib_global_search"),
            data={
                "code": "34120",
                "what": "croissants",
            },
            follow=True,
        ).content.decode()

    return _factory


def test_owner_published_listed(data, test_response):
    data.erp.published = True
    data.erp.save()
    response_content = test_response(data.niko)

    assert "Voir cet établissement" in response_content


def test_user_published_listed(data, test_response):
    data.erp.published = True
    data.erp.save()
    response_content = test_response(data.sophie)

    assert "Voir cet établissement" in response_content


def test_delete_similar_draft(mocker, data, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    data.erp.published = False
    data.erp.save()

    erp2 = deepcopy(data.erp)
    erp2.pk = None
    erp2.uuid = uuid.uuid4()
    erp2.save()

    access2 = deepcopy(data.erp.accessibilite)
    access2.pk = None
    access2.erp = erp2
    access2.save()

    client.force_login(data.sophie)
    client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp2.slug}),
        data={
            "published": "on",
        },
        follow=True,
    )

    mock_mail.assert_called_once_with(
        to_list=data.erp.user.email,
        template="draft_deleted",
        context={"commune": "Jacou", "draft_nom": "Aux bons croissants", "erp_url": erp2.get_absolute_uri()},
    )

    with pytest.raises(Erp.DoesNotExist):
        data.erp.refresh_from_db()

    erp2.refresh_from_db()
    assert erp2.published is True
