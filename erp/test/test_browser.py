# fmt: off
import pytest

from django.test import Client
from django.urls import reverse

from ..models import Commune, Erp


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, status_code",
    [
        (reverse("home"), 200),
        (reverse("mentions_legales"), 200),
        (reverse("accessibilite"), 200),
        (reverse("contact"), 200),
        (reverse("donnees_personnelles"), 200),
        (reverse("autocomplete"), 200),
        (reverse("commune", kwargs=dict(commune="invalid")), 404),
        (reverse("commune_activite", kwargs=dict(commune="invalid", activite_slug="invalid")), 404),
        (reverse("commune_erp", kwargs=dict(commune="invalid", erp_slug="invalid")), 404),
        (reverse("commune_activite_erp", kwargs=dict(commune="invalid", activite_slug="invalid", erp_slug="invalid")), 404),
    ],
)
def test_urls_ok(url, status_code, client):
    response = client.get(url)
    assert response.status_code == status_code
