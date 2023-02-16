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
