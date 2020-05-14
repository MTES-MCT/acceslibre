import pytest

from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from ..models import Activite, Commune, Erp


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def data(db):
    jacou = Commune.objects.create(
        nom="Jacou", departement="34", geom=Point((3.9047933, 43.6648217))
    )
    boulangerie = Activite.objects.create(nom="Boulangerie")
    return Erp.objects.create(
        nom="Aux bons croissants",
        numero="4",
        voie="grand rue",
        code_postal="34830",
        commune="Jacou",
        commune_ext=jacou,
        geom=Point((3.9047933, 43.6648217)),
        activite=boulangerie,
        published=True,
    )


def test_home_communes(data, client):
    response = client.get(reverse("home"))
    assert response.context["search"] is None
    assert len(response.context["communes"]) == 1
    assert response.context["communes"][0].nom == "Jacou"
    assert len(response.context["latest"]) == 0  # note: car accessibilité absente
    assert response.context["search_results"] == None


def test_home_search(data, client):
    response = client.get(reverse("home") + "?q=croissant%20jacou")
    assert response.context["search"] == "croissant jacou"
    print(response.context["search_results"])
    assert len(response.context["search_results"]["erps"]) == 1
    assert response.context["search_results"]["erps"][0].nom == "Aux bons croissants"


@pytest.mark.parametrize(
    "url",
    [
        # Home and search engine
        reverse("home"),
        reverse("home") + "?q=plop",
        # Editorial
        reverse("accessibilite"),
        reverse("autocomplete"),
        reverse("contact"),
        reverse("donnees_personnelles"),
        reverse("mentions_legales"),
        # App
        reverse("commune", kwargs=dict(commune="34-jacou")),
        reverse(
            "commune_activite",
            kwargs=dict(commune="34-jacou", activite_slug="boulangerie"),
        ),
        reverse(
            "commune_activite_erp",
            kwargs=dict(
                commune="34-jacou",
                activite_slug="boulangerie",
                erp_slug="aux-bons-croissants",
            ),
        ),
    ],
)
def test_urls_ok(data, url, client):
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        reverse("commune", kwargs=dict(commune="invalid")),
        reverse(
            "commune_activite", kwargs=dict(commune="invalid", activite_slug="invalid")
        ),
        reverse(
            "commune_activite_erp",
            kwargs=dict(commune="invalid", activite_slug="invalid", erp_slug="invalid"),
        ),
    ],
)
def test_urls_404(data, url, client):
    response = client.get(url)
    assert response.status_code == 404
