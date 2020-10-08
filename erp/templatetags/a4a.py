from django import template

from erp import naf
from erp import public_erp
from erp import schema
from erp import sirene

register = template.Library()


@register.filter(name="active_compte_section")
def active_compte_section(path, test):
    # There should REALLY be a way to retrieve a route name from a request. sigh.
    # So. Don't forget to update this code whenever we update these urls in erp.urls.
    active = any(
        [
            test == "mon_compte" and path == "/mon_compte/",
            test == "mes_erps" and path == "/mon_compte/erps/",
            test == "mes_contributions"
            and path.startswith("/mon_compte/contributions/"),
            test == "mot_de_passe"
            and path
            in [
                "/accounts/password_change/",
                "/accounts/password_change/done/",
                "/admin/password_change/",
                "/admin/password_change/done/",
            ],
        ]
    )
    if active:
        return "active"
    else:
        return ""


@register.filter(name="addclass")
def addclass(value, arg):
    try:
        return value.as_widget(attrs={"class": arg})
    except (AttributeError, TypeError, ValueError):
        return value


@register.filter(name="encode_etablissement_data")
def encode_etablissement_data(value):
    return sirene.base64_encode_etablissement(value)


@register.filter(name="encode_public_erp_data")
def encode_public_erp_data(value):
    return public_erp.base64_encode_etablissement(value)


@register.filter(name="format_distance")
def format_distance(value):
    if isinstance(value, str):
        return value
    if value.m == 0:
        return "Au même endroit"
    elif value.m > 999:
        return f"À {value.km:.2f} km"
    else:
        return f"À {round(value.m)} m"


@register.filter(name="format_siret")
def format_siret(value):
    return sirene.format_siret(value, separator=" ")


@register.filter(name="get_equipement_label")
def get_equipement_label(value):
    return dict(schema.EQUIPEMENT_MALENTENDANT_CHOICES).get(value, "Inconnu")


@register.filter(name="get_equipement_description")
def get_equipement_description(value):
    return dict(schema.EQUIPEMENT_MALENTENDANT_DESCRIPTIONS).get(value, "")


@register.filter(name="get_naf_label")
def get_naf_label(value):
    return naf.get_naf_label(value, "inconnu")


@register.filter("isemptylist")
def isemptylist(value):
    return value == []


@register.filter("isnonemptylist")
def isnonemptylist(value):
    return isinstance(value, list) and len(value) > 0


@register.filter("safe_username")
def safe_username(value):
    if "@" in value:
        username = value.split("@")[0]
        return username + "@..." if username else value.replace("@", "")
    return value


@register.filter("startswith")
def startswith(value, starts):
    if isinstance(value, str):
        return value.startswith(starts)
    return False
