import pytest
from django.contrib.gis.geos import Point

from erp.provider import geocoder


def test_ban_autocomplete_empty(mocker):
    mocker.patch("erp.provider.geocoder.query", return_value={"features": []})

    assert geocoder.autocomplete("plop") is None


def test_ban_autocomplete_ok(mocker):
    mocker.patch(
        "erp.provider.geocoder.query",
        return_value={"features": [{"geometry": {"coordinates": [1, 2]}}]},
    )

    assert geocoder.autocomplete("plop") == Point(1, 2, srid=4326)


def test_ban_autocomplete_request_error(mocker):
    mocker.patch("erp.provider.geocoder.query", side_effect=RuntimeError("error"))
    geocoder.autocomplete("plop") is None


@pytest.mark.disable_geocode_autouse
def test_geocode_fallback(mocker):
    def _result(*args, **kwargs):
        if kwargs.get("provider").value == "ban":  # FIXME Python3.11 can drop .value
            # Empty response from BAN
            return {}

        # Non empty response from geoportail
        return {"features": [{"geometry": {"coordinates": [1, 2]}, "properties": {"score": 1, "type": "housenumber"}}]}

    mocker.patch.object(geocoder, "query", side_effect=_result)
    response = geocoder.geocode("8, rue des palmiers 26000 Valence", provider=None)
    assert response["provider"] == "geoportail"
