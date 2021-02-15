import pytest

from django.contrib.gis.measure import Distance

from erp.templatetags import a4a


@pytest.mark.parametrize(
    "value, expected",
    [
        ("foo", "foo"),
        (Distance(m=0), "Au même endroit"),
        (Distance(m=22), "À 22 m"),
        (Distance(m=1222), "À 1222 m"),
        (Distance(m=1802), "À 1.80 km"),
        (Distance(km=42), "À 42 km"),
        (Distance(km=42.8), "À 43 km"),
    ],
)
def test_format_distance(value, expected):
    assert a4a.format_distance(value) == expected
