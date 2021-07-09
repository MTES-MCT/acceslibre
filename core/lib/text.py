import random
import string
import unicodedata

from django.contrib.gis.geos import Point


FRENCH_STOPWORDS = "le,la,les,au,aux,de,du,des,et".split(",")


def contains_digits(string):
    return any(char.isdigit() for char in string)


def contains_sequence(test, source):
    if not test or not source:
        return False
    return remove_accents(test.lower()) in remove_accents(source.lower())


def contains_sequence_any(tests, source):
    if not tests or not source:
        return False
    return any(contains_sequence(test, source) for test in tests)


def humanize_value(value, choices=None):
    """
    Get python value and returns a human readable version of it.
    """
    _humanize_empty_label = lambda x: "Vide" if len(x) == 0 else x
    if choices and (isinstance(value, (bool, str, tuple, list)) or value is None):
        value = [value] if not isinstance(value, (tuple, list)) else value
        return _humanize_empty_label(", ".join(dict(choices).get(v) for v in value))
    elif isinstance(value, (tuple, list)):
        return _humanize_empty_label(", ".join(value))
    elif isinstance(value, str):
        return _humanize_empty_label(value)
    elif isinstance(value, Point):
        return "%.4f, %.4f" % (value.y, value.x)
    elif value is None:
        return "Vide"
    elif value is True:
        return "Oui"
    elif value is False:
        return "Non"
    elif isinstance(value, (int, float)):
        return str(value)
    raise NotImplementedError("Type of value isn't recognized : %s" % type(value))


def normalize_nom(nom):
    parts = map(
        lambda x: x.title() if x not in FRENCH_STOPWORDS else x,
        nom.lower().split(" "),
    )
    return ucfirst(" ".join(parts))


def random_string(length):
    return "".join(random.choice(string.ascii_letters) for i in range(length))


def remove_accents(input_str):
    # see https://stackoverflow.com/a/517974/330911
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def strip_if_str(value):
    "Strips a value when it's a string, otherwise return it."
    return value.strip() if isinstance(value, str) else value


def ucfirst(string):
    return string if not string else string[0].upper() + string[1:]
