import pytest

from erp.provider import entreprise

from tests.fixtures import data


@pytest.fixture
def sample_feature():
    return {
        "activite_principale_entreprise": "6202A",
        "activite_principale": "6202A",
        "code_postal": "34830",
        "departement_commune_siege": "34120",
        "departement": "34",
        "email": None,
        "enseigne": None,
        "geo_adresse": "4 Grand Rue 34830 Jacou",
        "id": 63015890,
        "indice_repetition": None,
        "l1_normalisee": "AKEI",
        "latitude": "43.657028",
        "libelle_commune": "JACOU",
        "libelle_voie": "GRAND RUE",
        "longitude": "3.913557",
        "nom_raison_sociale": "AKEI",
        "numero_voie": "4",
        "siret": "88076068100010",
        "type_voie": None,
    }


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


def test_parse_etablissement_jacou_data_ok(data, sample_feature):
    # Note: Jacou Commune record is provided by the data fixture
    assert entreprise.parse_etablissement(sample_feature) == {
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


def test_parse_etablissement_jacou_missing_data(db, sample_feature):
    feature_with_missing_code_postal = sample_feature.copy()
    feature_with_missing_code_postal.pop("code_postal")
    assert entreprise.parse_etablissement(feature_with_missing_code_postal) is None

    feature_with_missing_commune = sample_feature.copy()
    feature_with_missing_commune.pop("libelle_commune")
    assert entreprise.parse_etablissement(feature_with_missing_commune) is None


def test_normalize_commune_ext(data):
    assert entreprise.normalize_commune("34120") == "Jacou"


def test_normalize_commune_arrondissement():
    assert entreprise.normalize_commune("75104") == "Paris"


def test_reorder_results():
    sample_features = [
        {"commune": "NIMES", "code_postal": "30000"},
        {"commune": "JACOU", "code_postal": "34830"},
    ]
    assert entreprise.reorder_results(sample_features, "restaurants jacou") == [
        {"commune": "JACOU", "code_postal": "34830"},
        {"commune": "NIMES", "code_postal": "30000"},
    ]
