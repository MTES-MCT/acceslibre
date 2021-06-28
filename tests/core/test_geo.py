import pytest

from core.lib import geo


def test_lonlat_to_latlon():
    assert geo.lonlat_to_latlon([1, 2]) == [2, 1]
    assert geo.lonlat_to_latlon([[1, 2], [3, 4]]) == [[4, 3], [2, 1]]
