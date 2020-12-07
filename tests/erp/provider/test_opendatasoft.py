import pytest

from erp.provider import opendatasoft


@pytest.fixture
def sample_response():
    return {
        "recordid": "40764d119d4d8fbdd7e7af20e96a50afaf661d99",
        "fields": {
            "siret": "88076068100010",
            "etatadministratifetablissement": "Actif",
            "geolocetablissement": [43.657028, 3.913557],
            "activiteprincipaleunitelegale": "62.02A",
            "activiteprincipaleetablissement": "62.02A",
            "denominationunitelegale": "AKEI",
            "l1_adressage_unitelegale": "AKEI",
            "adresseetablissement": "4 GRAND RUE",
            "numerovoieetablissement": "4",
            "libellevoieetablissement": "GRAND RUE",
            "codepostaletablissement": "34830",
            "libellecommuneetablissement": "JACOU",
            "codecommuneetablissement": "34120",
        },
    }


def test_build_query_params_std():
    params = opendatasoft.build_query_params("akei", "34120")
    assert params["q"] == "akei"
    assert params["refine.codecommuneetablissement"] == "34120"


def test_build_query_params_district():
    # Paris code_insee
    params = opendatasoft.build_query_params("abc", "75056")
    assert params["q"] == "abc Paris"
    assert "refine.codecommuneetablissement" not in params

    # Marseille code_insee
    params = opendatasoft.build_query_params("abc", "13055")
    assert params["q"] == "abc Marseille"
    assert "refine.codecommuneetablissement" not in params

    # Lyon code_insee
    params = opendatasoft.build_query_params("abc", "69123")
    assert params["q"] == "abc Lyon"
    assert "refine.codecommuneetablissement" not in params


def test_parse_etablissement_jacou_data_ok(sample_response):
    assert opendatasoft.parse_etablissement(sample_response) == {
        "source": "opendatasoft",
        "source_id": "40764d119d4d8fbdd7e7af20e96a50afaf661d99",
        "actif": True,
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
        "activite": None,
        "nom": "Akei",
        "siret": "88076068100010",
        "numero": "4",
        "voie": "GRAND RUE",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "JACOU",
        "code_insee": "34120",
    }
