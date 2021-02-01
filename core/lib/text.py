import random
import string
import unicodedata


FRENCH_STOPWORDS = "le,la,les,au,aux,de,du,des,et".split(",")


def contains_digits(string):
    return any(char.isdigit() for char in string)


def extract_numero_voie(string):
    """This attempts at extracting the street number and street name out
    of a French address string:

    >>> extract_numero_voie("4 bis rue yolo")
    ("4bis", "rue yolo")
    >>> extract_numero_voie("RN 7")
    (None, "RN 7")
    """
    if not string or len(string) == 0:
        return (None, "")
    if not string[0].isdigit():
        return (None, string)
    numero = None
    voie = None
    parts = string.replace(",", "").split(" ")
    if len(parts) == 1:
        voie = string
    elif len(parts) == 2:
        numero = parts[0]
        voie = " ".join(parts[1:])
    elif len(parts) >= 3:
        if parts[1].lower() in ("b", "bis", "t", "ter", "q", "quater"):
            numero = parts[0] + parts[1]
            voie = " ".join(parts[2:])
        else:
            numero = parts[0]
            voie = " ".join(parts[1:])
    return (numero, voie)


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
