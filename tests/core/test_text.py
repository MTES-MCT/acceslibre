import pytest

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


def test_contains_sequence_any():
    assert text.contains_sequence_any(["foo", "baz"], "föo bâr bÄz") is True
    assert text.contains_sequence_any(["foo", "nope"], "föo bâr bÄz") is True
    assert text.contains_sequence_any(["nope", "nope"], "föo bâr bÄz") is False


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, "Oui"),
        (False, "Non"),
        (None, "Vide"),
        (1, "1"),
        (0, "0"),
        (0.2, "0.2"),
        ("dpt", "dpt"),
        (["dpt", "dpt"], "dpt, dpt"),
    ],
)
def test_humanize_value_ok(value, expected):
    assert text.humanize_value(value) == expected


def test_humanize_value_ko():
    with pytest.raises(NotImplementedError):
        assert text.humanize_value(["dpt", True, 12])
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
