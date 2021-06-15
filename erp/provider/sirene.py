from stdnum.fr import siret
from stdnum import exceptions as stdnum_ex


def format_siret(value, separator=""):
    return siret.format(value, separator=separator)


def validate_siret(value):
    try:
        return siret.validate(value)
    except stdnum_ex.ValidationError:
        return None
