import json

import pytest
from django.contrib.gis.geos import MultiPolygon, Point

from core.lib import geo


@pytest.fixture
def mpoly():
    return """{
        "type": "MultiPolygon",
        "coordinates": [
            [ [ [102.0, 2.0], [103.0, 2.0], [103.0, 3.0], [102.0, 3.0], [102.0, 2.0] ]
            ],
            [ [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0] ],
              [ [100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2] ]
            ]
        ]
    }"""


@pytest.fixture
def poly():
    return """{
        "type": "Polygon",
        "coordinates": [
            [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0] ],
            [ [100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2] ]
        ]
    }"""


def test_geojson_mpoly_from_MultiPolygon(mpoly):
    assert isinstance(geo.geojson_mpoly(mpoly), MultiPolygon)
    assert isinstance(geo.geojson_mpoly(json.loads(mpoly)), MultiPolygon)


def test_geojson_mpoly_from_Polygon(poly):
    assert isinstance(geo.geojson_mpoly(poly), MultiPolygon)
    assert isinstance(geo.geojson_mpoly(json.loads(poly)), MultiPolygon)


def test_lonlat_to_latlon():
    assert geo.lonlat_to_latlon([1, 2]) == [2, 1]
    assert geo.lonlat_to_latlon([[1, 2], [3, 4]]) == [[4, 3], [2, 1]]


def test_parse_location():
    # (lat, lon) tuple arg
    assert isinstance(geo.parse_location((1, 2)), Point)
    assert geo.parse_location((1, 2)).coords == Point(2, 1).coords
    assert geo.parse_location(("1", "2")).coords == Point(2, 1).coords
    assert geo.parse_location(("1.2", "2.3")).coords == Point(2.3, 1.2).coords
    with pytest.raises(RuntimeError):
        geo.parse_location(None)
    with pytest.raises(RuntimeError):
        geo.parse_location(("bleh", "huh"))
    # Point arg
    assert isinstance(geo.parse_location(Point(1, 2)), Point)
    assert geo.parse_location(Point(1, 2)).coords == Point(1, 2).coords
