import pytest
from django.contrib.gis.geos import Point

from core.lib import text


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", False),
        ("1", True),
        ("123", True),
        ("12a", True),
        ("abcdefghijklmn", False),
    ],
)
def test_contains_digits(value, expected):
    assert text.contains_digits(value) is expected


@pytest.mark.parametrize(
    "test, source, expected",
    [
        ("", "", False),
        ("", "x", False),
        ("bar", "foo bar baz", True),
        ("baz", "foo bar baz", True),
        ("foo bar", "foo bar baz", True),
        ("foo bar", "Foo Bar", True),
        ("fôÔ Bar", "FöÔ bÂr Bâz", True),
        ("foo baz", "foo bar", False),
        ("foo bar", "foobar", False),
    ],
)
def test_contains_sequence(test, source, expected):
    assert text.contains_sequence(test, source) is expected


@pytest.mark.parametrize(
    "value, expected, choices",
    [
        (True, "Oui", None),
        (False, "Non", None),
        (None, "Inconnu", None),
        ("", "Inconnu", None),
        ([], "Inconnu", None),
        ((), "Inconnu", None),
        (1, "1", None),
        (0, "0", None),
        (0.2, "0.2", None),
        ("dpt", "dpt", None),
        (["dpt", "dpt"], "dpt, dpt", None),
        (True, "Oui", [(True, "Oui"), (False, "Non")]),
        ("dpt", "DPT", [("dpt", "DPT"), ("foo", "Foo")]),
        (["foo", "bar"], "FOO, BAR", [("foo", "FOO"), ("bar", "BAR")]),
        (Point(x=5.2607112131234, y=45.9110012214), "45.9110, 5.2607", None),
        ([None, False], "Vide, Non", [(None, "Vide"), (False, "Non")]),
        (["aucun"], "aucun", [("a", 1), ("b", 2)]),
    ],
)
def test_humanize_value_ok(value, expected, choices):
    assert text.humanize_value(value, choices=choices) == expected


def test_humanize_value_ko():
    with pytest.raises(NotImplementedError):
        assert text.humanize_value({"for": "bar"})


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", ""),
        ("abcdef", "abcdef"),
        ("ce bel été", "ce bel ete"),
        ("ôÖ", "oO"),
        ("À@äùéèïî", "A@aueeii"),
    ],
)
def test_remove_accents(value, expected):
    assert text.remove_accents(value) == expected


def test_ucfirst():
    assert text.ucfirst("") == ""
    assert text.ucfirst("a") == "A"
    assert text.ucfirst("foo") == "Foo"


def test_strip_if_str():
    assert text.strip_if_str(None) is None
    assert text.strip_if_str(" foo ") == "foo"
