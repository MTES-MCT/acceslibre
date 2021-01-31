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


def test_extract_numero_voie():
    cases = [
        ("", (None, "")),
        ("4 grand rue", ("4", "grand rue")),
        ("grand rue", (None, "grand rue")),
        ("4TER grand rue", ("4TER", "grand rue")),
    ]
    for case in cases:
        assert text.extract_numero_voie(case[0]) == case[1]


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
