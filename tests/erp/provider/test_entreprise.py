import pytest

from erp.provider import entreprise

from tests.fixtures import data


def test_format_coordonnees():
    assert entreprise.format_coordonnees({}) is None
    assert (
        entreprise.format_coordonnees({"latitude": "43.2", "longitude": None}) is None
    )
    assert entreprise.format_coordonnees({"latitude": None, "longitude": "3.1"}) is None
    assert [3.1, 43.2,] == entreprise.format_coordonnees(
        {"latitude": "43.2", "longitude": "3.1"}
    )


def test_format_email():
    assert entreprise.format_email({"email": None}) is None
    assert entreprise.format_email({"email": "https://plop"}) is None
    assert entreprise.format_email({"email": "toto@toto.com"}) == "toto@toto.com"


def test_format_naf():
    assert entreprise.format_naf({}) is None
    assert (
        entreprise.format_naf({"activite_principale_entreprise": "6202A"}) == "62.02A"
    )


def test_format_source_id():
    with pytest.raises(RuntimeError):
        assert entreprise.format_source_id({}, [])
    assert entreprise.format_source_id({}, ["a", "B", "c"]) == "a-b-c"


def test_retrieve_code_insee(data):
    assert entreprise.retrieve_code_insee({}) is None

    # Note: Jacou Commune record is provided by the data fixture
    assert (
        entreprise.retrieve_code_insee({"departement_commune_siege": "34120"})
        == "34120"
    )
    assert (
        entreprise.retrieve_code_insee(
            {"code_postal": "34830", "libelle_commune": "JACOU"}
        )
        == "34120"
    )


def test_parse_etablissement_jacou(db):
    feature = {
        "id": 63015890,
        "siret": "88076068100010",
        "l1_normalisee": "AKEI",
        "numero_voie": "4",
        "indice_repetition": None,
        "type_voie": None,
        "libelle_voie": "GRAND RUE",
        "code_postal": "34830",
        "departement": "34",
        "libelle_commune": "Jacou",
        "enseigne": None,
        "activite_principale": "6202A",
        "nom_raison_sociale": "AKEI",
        "departement_commune_siege": "34120",
        "email": None,
        "activite_principale_entreprise": "6202A",
        "longitude": "3.913557",
        "latitude": "43.657028",
        "geo_adresse": "4 Grand Rue 34830 Jacou",
    }
    assert entreprise.parse_etablissement(feature) == {
        "source": "entreprise_api",
        "source_id": "63015890",
        "actif": True,
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
        "activite": None,
        "nom": "AKEI",
        "siret": "88076068100010",
        "numero": "4",
        "voie": "GRAND RUE",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "34120",
        "contact_email": None,
        "telephone": None,
        "site_internet": None,
    }


def test_reorder_results():
    sample_results = [
        {"commune": "NIMES", "code_postal": "30000"},
        {"commune": "JACOU", "code_postal": "34830"},
    ]
    assert entreprise.reorder_results(sample_results, "restaurants jacou") == [
        {"commune": "JACOU", "code_postal": "34830"},
        {"commune": "NIMES", "code_postal": "30000"},
    ]
