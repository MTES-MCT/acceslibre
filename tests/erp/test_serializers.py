import pytest

from erp import serializers


@pytest.fixture
def sample_encoded_data_with_coords():
    return {
        "source": "entreprise_api",
        "source_id": "63015890",
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
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


def test_serializers_coords(sample_encoded_data_with_coords):
    encoded = serializers.encode_provider_data(sample_encoded_data_with_coords)
    decoded = serializers.decode_provider_data(encoded)

    for key, value in sample_encoded_data_with_coords.items():
        assert decoded[key] == value

    assert "activite" not in decoded
    assert decoded["lon"] == 3.913557
    assert decoded["lat"] == 43.657028


@pytest.fixture
def sample_encoded_data_with_lat_lon():
    return {
        "source": "entreprise_api",
        "source_id": "63015890",
        "naf": "62.02A",
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
        "lat": "43.657028",
        "lon": "3.913557",
    }


def test_serializers_lat_lon(sample_encoded_data_with_lat_lon):
    encoded = serializers.encode_provider_data(sample_encoded_data_with_lat_lon)
    decoded = serializers.decode_provider_data(encoded)

    for key, value in sample_encoded_data_with_lat_lon.items():
        assert decoded[key] == value

    assert "activite" not in decoded
    assert decoded["lon"] == "3.913557"
    assert decoded["lat"] == "43.657028"
