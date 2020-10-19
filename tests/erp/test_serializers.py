import pytest

from django.contrib.gis.geos import Point

from erp import serializers


@pytest.fixture
def sample_result():
    return {
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


def test_serializers(sample_result):
    encoded = serializers.encode_provider_data(sample_result)
    decoded = serializers.decode_provider_data(encoded)

    for key, value in sample_result.items():
        assert decoded[key] == value

    assert decoded["geom"] == Point([3.913557, 43.657028])
