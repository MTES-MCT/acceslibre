from unittest.mock import MagicMock, Mock

import pytest

from erp.provider import entreprise
from tests.factories import CommuneFactory


@pytest.fixture
def sample_response():
    return {
        "id": 63015890,
        "siret": "88076068100010",
        "activite_principale_entreprise": "6202A",
        "activite_principale": "6202A",
        "geo_adresse": "4 Grand Rue 34830 Jacou",
        "latitude": "43.657028",
        "longitude": "3.913557",
        "departement": "34",
        "code_commune": "34120",
        "code_postal": "34830",
        "numero_voie": "4",
        "type_voie": None,
        "indice_repetition": None,
        "libelle_commune": "JACOU",
        "libelle_voie": "GRAND RUE",
        "email": None,
        "unite_legale": {"denomination": "AKEI"},
    }


@pytest.mark.django_db
def test_normalize_commune_ext():
    CommuneFactory(nom="Jacou", code_insee="34120")
    assert entreprise.normalize_commune("34120") == "Jacou"


def test_normalize_commune_arrondissement():
    assert entreprise.normalize_commune("75104") == "Paris"


def test_reorder_results():
    sample_responses = [
        {"commune": "NIMES", "code_postal": "30000"},
        {"commune": "JACOU", "code_postal": "34830"},
    ]
    assert entreprise.reorder_results(sample_responses, "restaurants jacou") == [
        {"commune": "JACOU", "code_postal": "34830"},
        {"commune": "NIMES", "code_postal": "30000"},
    ]


@pytest.mark.django_db
def test_search(mocker):
    mocker.patch(
        "requests.get",
        return_value=MagicMock(
            url="",
            status_code=200,
            json=Mock(
                side_effect=lambda: {
                    "results": [
                        {
                            "siren": "216900621",
                            "nom_complet": "COMMUNE DE COISE",
                            "nom_raison_sociale": "COMMUNE DE COISE",
                            "sigle": None,
                            "nombre_etablissements": 5,
                            "nombre_etablissements_ouverts": 3,
                            "siege": {
                                "activite_principale": "84.11Z",
                                "activite_principale_registre_metier": None,
                                "adresse": "HOTEL DE VILLE 69590 COISE",
                                "cedex": None,
                                "code_pays_etranger": None,
                                "code_postal": "69590",
                                "commune": "69062",
                                "complement_adresse": "HOTEL DE VILLE",
                                "coordonnees": "45.611594,4.455569",
                                "date_creation": "1983-03-01",
                                "date_debut_activite": "2008-01-01",
                                "departement": "69",
                                "distribution_speciale": None,
                                "est_siege": True,
                                "etat_administratif": "A",
                                "geo_adresse": "Impasse de la Guillermiere 69590 Coise",
                                "geo_id": "69062_iq1r8w",
                                "indice_repetition": None,
                                "latitude": "45.611594",
                                "libelle_cedex": None,
                                "libelle_commune": "COISE",
                                "libelle_commune_etranger": None,
                                "libelle_pays_etranger": None,
                                "libelle_voie": None,
                                "liste_enseignes": ["MAIRIE"],
                                "liste_finess": None,
                                "liste_id_bio": None,
                                "liste_idcc": ["5021"],
                                "liste_id_organisme_formation": None,
                                "liste_rge": None,
                                "liste_uai": None,
                                "longitude": "4.455569",
                                "nom_commercial": None,
                                "numero_voie": None,
                                "siret": "21690062100014",
                                "tranche_effectif_salarie": "02",
                                "type_voie": None,
                            },
                            "activite_principale": "84.11Z",
                            "categorie_entreprise": "PME",
                            "annee_categorie_entreprise": None,
                            "date_creation": "1983-03-01",
                            "date_mise_a_jour": "2023-05-06T13:27:00",
                            "dirigeants": [],
                            "etat_administratif": "A",
                            "nature_juridique": "7210",
                            "section_activite_principale": "O",
                            "tranche_effectif_salarie": "02",
                            "annee_tranche_effectif_salarie": None,
                            "statut_diffusion": "O",
                        },
                    ],
                    "total_results": 1,
                    "page": 1,
                    "per_page": 5,
                    "total_pages": 1,
                },
            ),
        ),
    )
    results = entreprise.search("mairie coise", "69062", "84.11Z")
    assert results == [
        {
            "nom": "COMMUNE DE COISE",
            "voie": None,
            "commune": "COISE",
            "code_postal": "69590",
            "lieu_dit": "",
            "coordonnees": ["4.455569", "45.611594"],
            "siret": "21690062100014",
            "code_insee": "69062",
            "numero": None,
        }
    ]
