import logging
from enum import StrEnum

import requests

from erp.provider.generic_geoloc import GeolocRequester
from erp.provider.osm import OSMRequester

logger = logging.getLogger(__name__)


class Provider(StrEnum):
    BAN = "ban"
    GEOPORTAIL = "geoportail"
    OSM = "osm"


PROVIDERS = [
    {
        "name": Provider.BAN,
        "requester": GeolocRequester,
    },
    {
        "name": Provider.GEOPORTAIL,
        "requester": GeolocRequester,
    },
    {
        "name": Provider.OSM,
        "requester": OSMRequester,
    },
]


def geocode(address, postcode=None, citycode=None, provider=None):
    """
    Geocode an address: obtain all the address parts and its geolocation details (lat/lon)

    If a provider is given, we check the address only on it, if no provider is given we check the address
    on all providers, stopping with the first answering.

    In all cases, the provider used is returned.
    """
    provider_name = provider or PROVIDERS[0]["name"]

    provider = next((p for p in PROVIDERS if p["name"] == provider_name))
    try:
        next_provider = PROVIDERS[PROVIDERS.index(provider) + 1]
    except IndexError:
        next_provider = None

    data = provider["requester"](provider).geocode(address, postcode, citycode)
    if not data and next_provider:
        return geocode(address, postcode=postcode, citycode=citycode, provider=next_provider["name"])

    return data


def parse_coords(coords):
    "Returns a (lat, lon) tuple or None from a string"
    if coords is None:
        return None
    try:
        rlat, rlon = coords.split(",")
        return (float(rlat), float(rlon))
    except (IndexError, ValueError, TypeError):
        return None


def geocode_commune(code_insee):
    res = requests.get(
        "https://geo.api.gouv.fr/communes",
        {
            "fields": "code,nom,departement,centre,surface,population,codesPostaux",
            "limit": "1",
            "code": code_insee,
        },
    )
    json = res.json()
    return json[0] if json else None
