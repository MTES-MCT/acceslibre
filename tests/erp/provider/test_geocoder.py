import pytest
from django.contrib.gis.geos import Point

from erp.provider import geocoder
from erp.provider.generic_geoloc import GeolocRequester
from erp.provider.osm import OSMRequester


def test_ban_autocomplete_empty(mocker):
    mocker.patch("erp.provider.generic_geoloc.GeolocRequester.query", return_value={"features": []})

    assert geocoder.autocomplete("plop") is None


def test_ban_autocomplete_ok(mocker):
    mocker.patch(
        "erp.provider.generic_geoloc.GeolocRequester.query",
        return_value={"features": [{"geometry": {"coordinates": [1, 2]}}]},
    )

    assert geocoder.autocomplete("plop") == Point(1, 2, srid=4326)


def test_ban_autocomplete_request_error(mocker):
    mocker.patch("erp.provider.generic_geoloc.GeolocRequester.query", side_effect=RuntimeError("error"))
    geocoder.autocomplete("plop") is None


@pytest.mark.disable_geocode_autouse
def test_geocode_fallback_geoportail(mocker):
    mocker.patch.object(GeolocRequester, "query")
    GeolocRequester.query.side_effect = [
        {},  # First call, empty response from BAN
        {
            "features": [{"geometry": {"coordinates": [1, 2]}, "properties": {"score": 1, "type": "housenumber"}}]
        },  # Second call, non empty response from geoportail
    ]
    response = geocoder.geocode("8, rue des palmiers 26000 Valence", provider=None)
    assert response["provider"] == "geoportail"


@pytest.mark.disable_geocode_autouse
def test_geocode_fallback_osm(mocker):
    mocker.patch.object(GeolocRequester, "query")
    GeolocRequester.query.side_effect = [
        {},  # First call, empty response from BAN
        {},  # Second call, empty response from geoportail
    ]
    mocker.patch.object(OSMRequester, "query")
    OSMRequester.query.return_value = {
        "features": [{"geometry": {"coordinates": [1, 2]}, "properties": {"osm_type": "node", "type": "house"}}]
    }

    response = geocoder.geocode("8, rue des palmiers 26000 Valence", provider=None)
    assert response["provider"] == "osm"


@pytest.mark.disable_geocode_autouse
def test_geocode_fallback_no_answer(mocker):
    mocker.patch.object(GeolocRequester, "query")
    GeolocRequester.query.side_effect = [
        {},  # First call, empty response from BAN
        {},  # Second call, non empty response from geoportail
    ]
    mocker.patch.object(OSMRequester, "query")
    OSMRequester.query.return_value = {}

    response = geocoder.geocode("8, rue des palmiers 26000 Valence", provider=None)
    assert response == {}
