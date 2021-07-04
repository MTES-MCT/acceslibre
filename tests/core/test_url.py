import pytest

from core.lib import url


@pytest.mark.parametrize(
    "params, expected",
    [
        (dict(foo="bar"), "?foo=bar"),
        (dict(foo=""), "?foo="),
        (dict(foo="None"), "?foo="),
        (dict(foo=None), "?foo="),
        (dict(foo=None, bar="baz"), "?foo=&bar=baz"),
        (dict(foo=None, bar=None), "?foo=&bar="),
        (dict(foo="None", bar="None"), "?foo=&bar="),
    ],
)
def test_encode_qs(params, expected):
    assert url.encode_qs(**params) == expected
