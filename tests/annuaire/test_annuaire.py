import pytest
from django.contrib.gis.geos import Point
from django.test import Client
from django.urls import reverse

from erp.models import Commune
from tests.factories import ErpFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def paris():
    return Commune.objects.create(
        nom="Paris",
        departement="75",
        code_insee="75056",
        code_postaux=[f"750{i:02d}" for i in range(1, 21)],
        geom=Point(2.3488, 48.8534),
    )


@pytest.fixture
def paris_arrondissements():
    return [
        Commune.objects.create(
            nom=f"Paris {i}{e} arrondissement",
            departement="75",
            code_insee=f"751{i:02d}",
            code_postaux=[f"750{i:02d}"],
            arrondissement=True,
            geom=Point(2.3488, 48.8534),
        )
        for i, e in ((1, "er"), (2, "e"))
    ]


@pytest.mark.django_db
def test_annuaire_home(client):
    assert client.get(reverse("annuaire_home")).status_code == 200


@pytest.mark.django_db
def test_annuaire_departement(client):
    assert client.get(reverse("annuaire_departement", kwargs={"departement": "34"})).status_code == 200


@pytest.mark.django_db
def test_annuaire_departement_missing(client):
    assert client.get(reverse("annuaire_departement", kwargs={"departement": "99999"})).status_code == 404


@pytest.mark.django_db
def test_annuaire_departement_commune_count(client):
    commune = Commune.objects.create(
        nom="Neufchâteau",
        departement="88",
        code_insee="88321",
        code_postaux=["88300"],
        geom=Point(5.6962, 48.3568),
    )
    ErpFactory(commune_ext=commune, code_postal="88300")
    ErpFactory(commune_ext=commune, code_postal="88300")
    ErpFactory(commune_ext=commune, code_postal="88300", published=False)

    response = client.get(reverse("annuaire_departement", kwargs={"departement": "88"}))

    assert response.status_code == 200
    assert response.context["communes"][0].erp_access_count == 2


@pytest.mark.django_db
def test_annuaire_departement_groupes_erps_par_arrondissement(client, paris, paris_arrondissements):
    # erps are mostly attached to the parent commune, not to their arrondissement
    for _ in range(2):
        ErpFactory(commune_ext=paris, code_postal="75001")
    ErpFactory(commune_ext=paris, code_postal="75002")
    ErpFactory(commune_ext=paris_arrondissements[1], code_postal="75002")

    response = client.get(reverse("annuaire_departement", kwargs={"departement": "75"}))

    assert response.status_code == 200
    communes = list(response.context["communes"])
    assert [commune.nom for commune in communes] == ["Paris"], "arrondissements must not be listed twice"
    parent = communes[0]
    # 3 erps attached to Paris + 1 already attached to the second arrondissement
    assert parent.erp_access_count == 4
    assert response.context["current_departement_erp_count"] == 4
    assert [arrondissement.erp_access_count for arrondissement in parent.arrondissements] == [2, 2]


@pytest.mark.django_db
def test_annuaire_departement_ignore_arrondissement_hors_parents(client, paris, paris_arrondissements):
    # an arrondissement whose parent has no erp stays in the flat list, with its own count
    ErpFactory(commune_ext=paris_arrondissements[0], code_postal="75001")

    response = client.get(reverse("annuaire_departement", kwargs={"departement": "75"}))

    assert response.status_code == 200
    communes = list(response.context["communes"])
    assert [commune.nom for commune in communes] == ["Paris 1er arrondissement"]
    assert communes[0].erp_access_count == 1
