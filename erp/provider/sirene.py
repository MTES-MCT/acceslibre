from stdnum import exceptions as stdnum_ex
from stdnum.fr import siret


def format_siret(value, separator=""):
    return siret.format(value, separator=separator)


def validate_siret(value):
    try:
        return siret.validate(value)
    except stdnum_ex.ValidationError:
        return None
