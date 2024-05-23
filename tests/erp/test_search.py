from urllib.parse import urlencode

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from erp.models import Accessibilite, Erp
from erp.views import _clean_address
from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory


def test_search_clean_params(data, client):
    response = client.get(reverse("search") + "?where=None&what=None&lat=None&lon=None&code=None")
    assert response.context["where"] == "France entière"
    assert response.context["what"] == ""
    assert response.context["lat"] == ""
    assert response.context["lon"] == ""
    assert response.context["code"] == ""


def test_search_pagination(data, client):
    commune = CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
    data.erp.delete()
    for i in range(1, 102):
        erp = Erp.objects.create(
            nom=f"e{i}",
            commune_ext=commune,
            commune="jacou",
            geom=data.erp.geom,
            published=True,
        )
        Accessibilite.objects.create(erp=erp, sanitaires_presence=True)
    assert Erp.objects.published().count() == 101
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=1")
    assert response.status_code == 200
    assert response.context["pager"].paginator.num_pages == 3
    assert len(response.context["pager"]) == 50
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=2")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 50
    response = client.get(reverse("search") + "?where=jacou&code=34120&page=3")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 1
    assert "geojson_list" in response.context, "Missing info for map"


def test_search_pagination_performances(data, client, django_assert_max_num_queries):
    commune = CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
    data.erp.delete()
    erp = Erp.objects.create(
        nom="ERP",
        commune_ext=commune,
        commune="jacou",
        geom=data.erp.geom,
        published=True,
    )
    Accessibilite.objects.create(erp=erp, sanitaires_presence=True)

    with django_assert_max_num_queries(12):
        response = client.get(reverse("search") + "?where=jacou&code=34120&page=1")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 1

    for i in range(1, 10):
        erp = Erp.objects.create(
            nom=f"e{i}",
            commune_ext=commune,
            commune="jacou",
            geom=data.erp.geom,
            published=True,
        )
        Accessibilite.objects.create(erp=erp, sanitaires_presence=True)

    with django_assert_max_num_queries(12):
        response = client.get(reverse("search") + "?where=jacou&code=34120&page=1")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 10


def test_search_by_municipality(data, client):
    Erp.objects.create(
        nom="Out of town",
        commune="Lille",
        code_postal=59000,
        published=True,
    )
    filters = {
        "where": "Jacou (34830)",
        "search_type": "municipality",
        "postcode": 34830,
        "municipality": "Jacou",
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "Jacou (34830)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_search_by_municipality_with_multiple_postcodes_for_municipality(data, client):
    Erp.objects.create(
        nom="Out of town",
        commune="Lille",
        code_postal=59000,
        published=True,
    )
    Erp.objects.create(
        nom="Other postcode",
        commune="Jacou",
        code_postal=34831,
        published=True,
    )
    filters = {
        "where": "Jacou (34830)",
        "search_type": "municipality",
        "postcode": 34830,
        "municipality": "Jacou",
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "Jacou (34830)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_search_whole_country(data, client):
    Erp.objects.create(nom="Out of town", commune="Lille", code_postal=59000, published=True, activite=data.boulangerie)
    filters = {"what": "Boulangerie", "where": "France entière", "search_type": ""}
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "France entière"
    assert len(response.context["pager"]) == 2


def test_search_respects_what_clause(data, client):
    activite_mairie = ActiviteFactory(nom="Mairie")
    Erp.objects.create(
        nom="Different activity",
        commune=data.erp.commune,
        code_postal=data.erp.code_postal,
        published=True,
        activite=activite_mairie,
    )
    filters = {"what": "Boulangerie", "where": "France entière", "search_type": ""}
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "France entière"
    assert len(response.context["pager"]) == 1


def test_search_exact_housenumber(data, client):
    Erp.objects.create(
        nom="Different city",
        commune="Lille",
        code_postal=59000,
        published=True,
        activite=data.boulangerie,
    )
    filters = {
        "what": "Boulangerie",
        "where": "4 grand rue 34830 Jacou",
        "lat": 43.6648217,
        "lon": 3.9047933,
        "postcode": 34830,
        "search_type": "housenumber",
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "4 grand rue 34830 Jacou"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"

    # Test that is still work with a slight tolerance, here offset on longitude
    filters = {
        "what": "Boulangerie",
        "where": "15 grand rue 34830 Jacou",
        "lat": 43.6648217,
        "lon": 3.9067933,
        "postcode": 34830,
        "search_type": "housenumber",
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert len(response.context["pager"]) == 1


def test_search_street_name(data, client):
    Erp.objects.create(
        nom="Different city",
        commune="Lille",
        code_postal=59000,
        published=True,
        activite=data.boulangerie,
    )
    Erp.objects.create(
        nom="Same city other street",
        commune="Jacou",
        code_postal=34830,
        published=True,
        activite=data.boulangerie,
        voie="Avenue des Champs Elysées",
    )
    Erp.objects.create(
        nom="Same city same street",
        commune="Jacou",
        code_postal=34830,
        published=True,
        activite=data.boulangerie,
        voie="grand rue",
    )

    filters = {
        "what": "Boulangerie",
        "where": "4 grand rue 34830 Jacou",
        "lat": 43.6648217,
        "lon": 3.9047933,
        "postcode": 34830,
        "search_type": "street",
        "street_name": "Grand rue",
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "4 grand rue 34830 Jacou"
    assert len(response.context["pager"]) == 2
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_search_around_me(data, client):
    Erp.objects.create(
        nom="fake data",
        commune="Beuvry la foret",
        code_postal=59310,
        published=True,
        activite=data.boulangerie,
        geom=Point((3.2605877, 50.4569051)),
    )
    filters = {
        "what": "Boulangerie",
        "where": "Autour de moi (Rue des Arcins 59310 Beuvry-la-Forêt)",
        "search_type": "Autour de moi",
        "lat": 50.4569054,
        "lon": 3.2605877,
    }
    query_string = urlencode(filters)
    response = client.get(f"{reverse('search')}?{query_string}")
    assert response.status_code == 200
    assert response.context["where"] == "Autour de moi (Rue des Arcins 59310 Beuvry-la-Forêt)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "fake data"


def test_search_in_municipality(data, client):
    Erp.objects.create(
        nom="Out of town",
        commune="Lille",
        code_postal=59000,
        published=True,
    )
    response = client.get(reverse("search_commune", kwargs={"commune_slug": "34-jacou"}))
    assert response.context["where"] == "Jacou (34)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"


def test_search_in_municipality_performances(data, client, django_assert_max_num_queries):
    with django_assert_max_num_queries(9):
        response = client.get(reverse("search_commune", kwargs={"commune_slug": "34-jacou"}))
    assert len(response.context["pager"]) == 1

    for _ in range(5):
        Erp.objects.create(
            nom="ERP",
            code_postal="34830",
            commune="Jacou",
            commune_ext=data.erp.commune_ext,
            published=True,
            activite=data.erp.activite,
        )

    with django_assert_max_num_queries(9):
        response = client.get(reverse("search_commune", kwargs={"commune_slug": "34-jacou"}))
    assert len(response.context["pager"]) == 6


def test_search_in_municipality_respects_what_clause(data, client):
    activite_mairie = ActiviteFactory(nom="Mairie")
    Erp.objects.create(
        nom="Out of town",
        commune=data.erp.commune,
        code_postal=data.erp.code_postal,
        published=True,
        activite=activite_mairie,
    )
    base_url = reverse("search_commune", kwargs={"commune_slug": "34-jacou"})
    response = client.get(f"{base_url}?what=Boulangerie")
    assert response.context["where"] == "Jacou (34)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "Aux bons croissants"


@pytest.mark.parametrize(
    "where, expected",
    (
        ("Strasbourg", ("Strasbourg", "")),
        ("Paris (75)", ("Paris", "75")),
        ("10 Rue Marin 69160 Tassin-la-Demi-Lune", ("Tassin-la-Demi-Lune", "")),
    ),
)
def test_clean_address(where, expected):
    assert _clean_address(where) == expected


def test_search_in_municipality_not_found(data, client):
    response = client.get(reverse("search_commune", kwargs={"commune_slug": "31-foo"}))
    assert response.status_code == 404


def test_invalid_search_params_404(data, client):
    response = client.get(reverse("search") + "?where=&what=&lat=INVALID&lon=INVALID")
    assert response.status_code == 404


@pytest.mark.django_db
def test_search_in_municipality_with_identical_names(client):
    CommuneFactory(
        nom="Saint-Pierre",
        code_postaux=[
            "67140",
        ],
        departement="67",
    )
    CommuneFactory(
        nom="Saint-Pierre",
        code_postaux=[
            "97410",
        ],
        departement="974",
    )
    ErpFactory(nom="ERP en Outre Mer", published=True, commune="Saint-Pierre", code_postal="97410")
    ErpFactory(nom="ERP en métropole", published=True, commune="Saint-Pierre", code_postal="67140")
    response = client.get(reverse("search_commune", kwargs={"commune_slug": "974-saint-pierre"}))

    assert response.status_code == 200
    assert response.context["where"] == "Saint-Pierre (974)"
    assert len(response.context["pager"]) == 1
    assert response.context["pager"][0].nom == "ERP en Outre Mer"
