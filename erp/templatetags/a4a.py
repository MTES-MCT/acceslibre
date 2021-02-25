import json
import random

from datetime import datetime
from urllib.parse import quote

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

from erp import schema
from erp import serializers
from erp.models import Erp
from erp.provider import arrondissements, naf, sirene

register = template.Library()

DATA_SOURCES = dict(Erp.SOURCE_CHOICES)


@register.filter(name="active_compte_section")
def active_compte_section(path, test):
    # There should REALLY be a way to retrieve a route name from a request. sigh.
    # So. Don't forget to update this code whenever we update these urls in erp.urls.
    active = any(
        [
            test == "mon_compte" and path == "/mon_compte/",
            test == "mes_erps" and path == "/mon_compte/erps/",
            test == "mon_identifiant" and path == "/mon_compte/identifiant/",
            test == "mes_contributions"
            and path.startswith("/mon_compte/contributions/"),
            test == "mes_abonnements" and path.startswith("/mon_compte/abonnements/"),
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


@register.simple_tag
def arrondissements_json_data():
    return mark_safe(arrondissements.to_json())


@register.filter(name="encode_provider_data")
def encode_provider_data(value):
    return serializers.encode_provider_data(value)


@register.filter(name="format_distance")
def format_distance(value):
    if isinstance(value, str):
        return value
    if value.m == 0:
        return "Au même endroit"
    elif value.m < 1500:
        return f"À {round(value.m)} m"
    elif value.m < 10000:
        return f"À {value.km:.2f} km"
    else:
        return f"À {round(value.km)} km"


@register.filter(name="format_isodate")
def format_isodate(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


@register.filter(name="format_source")
def format_source(value, default="N/A"):
    return DATA_SOURCES.get(value, default)


@register.filter(name="format_username")
def format_username(value):
    username = safe_username(value)
    if username in schema.PARTENAIRES:
        info = schema.PARTENAIRES[username]
        avatar = f"/static/img/partenaires/{info['avatar']}"
        url = reverse("partenaires") + f"#{username}"
        return mark_safe(
            f"""
            <a href="{url}" title="En savoir plus sur {username}">
              <img src="{avatar}" alt="" width="16" height="16">&nbsp;{username}</a>
            </a>
            """
        )
    return username


@register.filter(name="format_siret")
def format_siret(value):
    return sirene.format_siret(value, separator=" ")


@register.filter(name="get_dispositifs_appel_label")
def get_dispositifs_appel_label(value):
    return dict(schema.DISPOSITIFS_APPEL_CHOICES).get(value, "")


@register.filter(name="get_equipement_label")
def get_equipement_label(value):
    return dict(schema.EQUIPEMENT_MALENTENDANT_CHOICES).get(value, "Inconnu")


@register.filter(name="get_equipement_description")
def get_equipement_description(value):
    return dict(schema.EQUIPEMENT_MALENTENDANT_DESCRIPTIONS).get(value, "")


@register.filter(name="get_label_name")
def get_label_name(value):
    return dict(schema.LABEL_CHOICES).get(value)


@register.filter(name="get_naf_label")
def get_naf_label(value):
    return naf.get_naf_label(value, "inconnu")


@register.filter("isemptylist")
def isemptylist(value):
    return value == []


@register.filter("isnonemptylist")
def isnonemptylist(value):
    return isinstance(value, list) and len(value) > 0


@register.simple_tag
def result_map_img(
    coordonnees, size="500x300", zoom=16, style="streets-v11", marker=True
):
    base = f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
    lat = coordonnees[1]
    lon = coordonnees[0]
    if marker:
        geojson = quote(json.dumps({"type": "Point", "coordinates": [lon, lat]}))
        marker_code = f"geojson({geojson})/"
    else:
        marker_code = ""
    return f"{base}{marker_code}{lon},{lat},{zoom},0,50/{size}?access_token={settings.MAPBOX_TOKEN}"


@register.filter("safe_username")
def safe_username(value):
    if "@" in value:
        username = value.split("@")[0]
        return username + "@..." if username else value.replace("@", "")
    return value


@register.filter
def shuffle(arg):
    tmp = list(arg)[:]
    random.shuffle(tmp)
    return tmp


@register.filter("startswith")
def startswith(value, starts):
    if isinstance(value, str):
        return value.startswith(starts)
    return False
