import random
import string
import unicodedata


FRENCH_STOPWORDS = "le,la,les,au,aux,de,du,des,et".split(",")


def contains_digits(string):
    return any(char.isdigit() for char in string)


def extract_numero_voie(string):
    if len(string) > 0 and string[0].isdigit():
        return tuple(string.split(" ", maxsplit=1))
    else:
        return (None, string)


def normalize_nom(nom):
    parts = map(
        lambda x: x.title() if x not in FRENCH_STOPWORDS else x,
        nom.lower().split(" "),
    )
    return ucfirst(" ".join(parts))


def random_string(self, length):
    return "".join(random.choice(string.ascii_letters) for i in range(length))


def remove_accents(input_str):
    # see https://stackoverflow.com/a/517974/330911
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def ucfirst(string):
    return string if not string else string[0].upper() + string[1:]
