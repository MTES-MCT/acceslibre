import pytest
import requests

from django.contrib.gis.geos import Point

from erp.provider import geocoder


# geocoder#autocomplete()


def test_autocomplete_empty(mocker, capsys):
    mocker.patch("erp.provider.geocoder.query", return_value={"features": []})

    assert geocoder.autocomplete("plop") is None


def test_autocomplete_ok(mocker, capsys):
    mocker.patch(
        "erp.provider.geocoder.query",
        return_value={"features": [{"geometry": {"coordinates": [1, 2]}}]},
    )

    assert geocoder.autocomplete("plop") == Point(1, 2, srid=4326)


def test_autocomplete_request_error(mocker, capsys):
    mocker.patch("erp.provider.geocoder.query", side_effect=RuntimeError("error"))
    geocoder.autocomplete("plop") is None


# geocoder#geocode()


def test_geocode_ok(mocker):
    mocker.patch(
        "erp.provider.geocoder.query",
        return_value={
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [2.309841, 48.844828]},
                    "properties": {
                        "label": "12 Rue Lecourbe 75015 Paris",
                        "score": 0.8956363636363637,
                        "housenumber": "12",
                        "id": "75115_5456_00012",
                        "name": "12 Rue Lecourbe",
                        "postcode": "75015",
                        "citycode": "75115",
                        "x": 649349.66,
                        "y": 6860752.66,
                        "city": "Paris",
                        "district": "Paris 15e Arrondissement",
                        "context": "75, Paris, Île-de-France",
                        "type": "housenumber",
                        "importance": 0.852,
                        "street": "Rue Lecourbe",
                    },
                }
            ]
        },
    )

    result = geocoder.geocode("test search")

    assert result["code_insee"] == "75115"
    assert result["code_postal"] == "75015"
    assert result["commune"] == "Paris"
    assert result["geom"] == Point(2.309841, 48.844828, srid=4326)
    assert result["lieu_dit"] is None
    assert result["numero"] == "12"
    assert result["voie"] == "Rue Lecourbe"


def test_geocode_error(mocker):
    mocker.patch(
        "requests.get",
        side_effect=requests.exceptions.RequestException("Boom"),
    )

    with pytest.raises(RuntimeError) as err:
        geocoder.geocode("xxx")
        assert "indisponible" in err.value.message
