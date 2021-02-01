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
    "value, expected",
    [
        ("", (None, "")),
        ("4 grand rue", ("4", "grand rue")),
        ("4, grand rue", ("4", "grand rue")),
        ("grand rue", (None, "grand rue")),
        ("4 bis r yolo", ("4bis", "r yolo")),
        ("4TER grand rue", ("4TER", "grand rue")),
        ("rn 7", (None, "rn 7")),
        ("chemin des prés", (None, "chemin des prés")),
    ],
)
def test_extract_numero_voie(value, expected, capsys):
    assert text.extract_numero_voie(value) == expected


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
