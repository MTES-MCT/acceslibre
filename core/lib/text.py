import datetime
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


def _humanize_map_choices(values, choices):
    labels = []
    for value in values:
        labels.append(str(choices.get(value)) if value in choices else str(value))
    return labels


def humanize_value(value, choices=None):
    """
    Get python value and returns a human readable version of it.
    """
    if choices and (isinstance(value, (bool, str, tuple, list)) or value is None):
        values = [value] if not isinstance(value, (tuple, list)) else value
        mapped_choices = _humanize_map_choices(values, dict(choices))
        value = ", ".join(mapped_choices)
    elif value is None:
        pass
    elif isinstance(value, (tuple, list)):
        value = ", ".join(value)
    elif isinstance(value, str):
        value = value
    elif isinstance(value, Point):
        value = "%.4f, %.4f" % (value.y, value.x)
    elif value is True:
        value = "Oui"
    elif value is False:
        value = "Non"
    elif isinstance(value, (int, float)):
        value = str(value)
    elif isinstance(value, datetime.datetime):
        value = value.strftime("%Y-%m-%d à %H:%M")
    else:
        raise NotImplementedError("Type of value isn't recognized : %s" % type(value))

    return "Inconnu" if value in ("", "None", None, [], ()) else value


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
