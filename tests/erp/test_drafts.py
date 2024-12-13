import uuid
from copy import deepcopy

import pytest
from django.test import Client
from django.urls import reverse

from erp.models import Erp
from tests.factories import CommuneFactory, ErpFactory, UserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_result():
    erp = ErpFactory(nom="Aux bons croissants", code_postal="34120")
    return {
        "exists": erp,
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


@pytest.mark.django_db
def test_delete_similar_draft(mocker, client):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    user = UserFactory()
    other_user = UserFactory()
    erp = ErpFactory(
        published=False,
        accessibilite__entree_porte_presence=True,
        accessibilite__transport_station_presence=True,
        accessibilite__stationnement_presence=True,
        accessibilite__stationnement_pmr=True,
        accessibilite__cheminement_ext_presence=True,
        user=user,
    )
    CommuneFactory(nom=erp.commune, departement=erp.code_postal[0:2])

    erp2 = deepcopy(erp)
    erp2.pk = None
    erp2.uuid = uuid.uuid4()
    erp2.save()

    access2 = deepcopy(erp.accessibilite)
    access2.pk = None
    access2.erp = erp2
    access2.save()

    client.force_login(other_user)
    client.post(
        reverse("contrib_publication", kwargs={"erp_slug": erp2.slug}),
        data={
            "published": "on",
        },
        follow=True,
    )

    mock_mail.assert_called_once_with(
        to_list=erp.user.email,
        template="draft_deleted",
        context={"commune": erp.commune, "draft_nom": erp.nom, "erp_url": erp2.get_absolute_uri()},
    )

    with pytest.raises(Erp.DoesNotExist):
        erp.refresh_from_db()

    erp2.refresh_from_db()
    assert erp2.published is True
