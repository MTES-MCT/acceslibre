import json
import random
from datetime import datetime
from urllib.parse import quote

import phonenumbers
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as translate

from erp import forms, schema, serializers
from erp.models import Erp
from erp.schema import FIELDS

register = template.Library()


@register.filter(name="active_compte_section")
def active_compte_section(path, test):
    # There should REALLY be a way to retrieve a route name from a request. sigh.
    # So. Don't forget to update this code whenever we update these urls in erp.urls.
    active = any(
        [
            test == "mon_compte" and path == "/compte/",
            test == "mes_erps" and path == "/compte/erps/",
            test == "mon_identifiant" and path == "/compte/identifiant/",
            test == "mon_email" and path.startswith("/compte/email/"),
            test == "mes_contributions" and path.startswith("/compte/contributions/"),
            test == "mes_challenges" and path.startswith("/compte/challenges/"),
            test == "mes_abonnements" and path.startswith("/compte/abonnements/"),
            test == "mes_preferences" and path.startswith("/compte/preferences/"),
            test == "mot_de_passe"
            and path
            in [
                "/compte/password_change/",
                "/compte/password_change/done/",
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


@register.filter(name="encode_provider_data")
def encode_provider_data(value):
    return serializers.encode_provider_data(value)


@register.filter(name="format_distance")
def format_distance(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, float):
        return str(value)

    unit = translate("kilomètres")
    if value.m == 0:
        return translate("Au même endroit")
    elif value.m < 1500:
        unit = translate("mètres")
        return mark_safe(f'À {round(value.m)}<i aria-hidden="true">m</i><i class="fr-sr-only"> {unit}</i>')
    elif value.m < 10000:
        formatted = f"{value.km:.2f}".replace(".", ",")
        return mark_safe(f'À {formatted}<i aria-hidden="true">km</i><i class="fr-sr-only"> {unit}</i>')
    else:
        return mark_safe(f'À {round(value.km)}<i aria-hidden="true">km</i><i class="fr-sr-only"> {unit}</i>')


@register.filter(name="format_isodate")
def format_isodate(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


@register.filter(name="format_phone")
def format_phone(value):
    if not value:
        return ""
    try:
        return phonenumbers.format_number(
            phonenumbers.parse(value, "FR"),
            phonenumbers.PhoneNumberFormat.NATIONAL,
        )
    except phonenumbers.phonenumberutil.NumberParseException:
        return value


@register.filter(name="format_username")
def format_username(value):
    username = safe_username(value)
    if username in schema.PARTENAIRES:
        info = schema.PARTENAIRES[username]
        avatar = f"/static/img/partenaires/{info['avatar']}"
        url = reverse("partenaires") + f"#{username}"
        title = translate("En savoir plus sur")
        return mark_safe(
            f"""
            <a href="{url}" title="{title} {username}">
              <img src="{avatar}" alt="" width="16" height="16">&nbsp;{username}</a>
            </a>
            """
        )
    return username


@register.filter(name="get_field_label")
def get_field_label(value):
    return schema.get_label(value) or forms.get_label(value)


@register.filter(name="positive_text")
def positive_text(value):
    try:
        field = FIELDS[value]
    except KeyError:
        return None
    if field.get("help_text_ui_v2"):
        return field.get("help_text_ui_v2")
    if field.get("help_text_ui"):
        return field.get("help_text_ui")
    return None


@register.filter(name="field_image_url")
def field_image_url(key, index=0):
    try:
        field = FIELDS[key]
        result = field.get("choices_images", [])[index]
        return result
    except (KeyError, IndexError):
        return None


@register.filter(name="should_display_label")
def should_display_label(field):
    return FIELDS.get(field, {}).get("should_display_label", True)


@register.filter(name="negative_text")
def negative_text(value):
    try:
        field = FIELDS[value]
    except KeyError:
        return None
    if field.get("help_text_ui_neg_v2"):
        return field.get("help_text_ui_neg_v2")
    if field.get("help_text_ui_neg"):
        return field.get("help_text_ui_neg")
    return None


@register.simple_tag
def access_text(value_name, access):
    value = getattr(access, value_name)
    if value is True:
        return positive_text(value_name)
    if value is False:
        return negative_text(value_name)


@register.inclusion_tag("erp/includes/access_value.html")
def render_access_value(value_name, access, filters=None):
    return {"value_name": value_name, "access": access, "value": getattr(access, value_name), "filters": filters}


@register.simple_tag
def render_field(value):
    return (isinstance(value, list) and len(value) > 0) or (
        not isinstance(value, list) and value != "" and value is not None
    )


@register.simple_tag
def retrieve_erp(value):
    if "/contrib/publication" in value:
        erp_slug = value.split("/contrib/publication/")[1].split("/")[0].strip("/")
        try:
            return Erp.objects.get(slug=erp_slug).nom
        except Erp.DoesNotExist:
            return None
    return None


@register.simple_tag
def result_map_img(coordonnees, size="500x300", zoom=16, style="streets-v11", marker=True):
    base = f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
    lat = coordonnees[1]
    lon = coordonnees[0]
    if marker:
        geojson = quote(json.dumps({"type": "Point", "coordinates": [lon, lat]}))
        marker_code = f"geojson({geojson})/"
    else:
        marker_code = ""
    return f"{base}{marker_code}{lon},{lat},{zoom},0,50/{size}?access_token={settings.MAPBOX_TOKEN}"


def safe_username(value):
    if "@" in value:
        username = value.split("@")[0]
        return username + "@..." if username else value.replace("@", "")
    return value


@register.filter
def shuffle(arg):
    tmp = list(arg)[:]
    tmp.sort(key=lambda item: random.randint(0, 99) + item[1].get("weight", 0), reverse=True)
    return tmp


@register.filter("startswith")
def startswith(value, starts):
    if isinstance(value, str):
        return value.startswith(starts)
    return False


@register.filter
def get_list(dictionary, key):
    if not isinstance(dictionary, dict):
        return []
    return dictionary.getlist(key)


@register.filter
def label_to_image(label):
    if label == "Destination pour Tous":
        return static("img/labels/dpt.jpg")
    if label == "Mobalib":
        return static("img/labels/mobalib.jpg")
    if label == "Tourisme & Handicap":
        return static("img/labels/th.jpg")
    if label == "Handiplage":
        return static("img/labels/handiplage.jpg")
