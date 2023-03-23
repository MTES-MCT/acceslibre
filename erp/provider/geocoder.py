import logging
from enum import Enum  # FIXME Python3.11 replace this with StrEnum

import requests
from django.contrib.gis.geos import Point

from core.lib import geo

logger = logging.getLogger(__name__)


class Provider(Enum):  # FIXME Python3.11 replace this with StrEnum
    BAN = "ban"
    GEOPORTAIL = "geoportail"


PROVIDER_URLS = {
    Provider.BAN: "https://api-adresse.data.gouv.fr/search/",
    Provider.GEOPORTAIL: "https://wxs.ign.fr/essentiels/geoportail/geocodage/rest/0.1/search",
}


def autocomplete(q, limit=1):
    params = {
        "autocomplete": 1,
        "q": q,
        "limit": limit,
    }
    try:
        results = query(params, timeout=0.75)  # avoid blocking for too long
        (lon, lat) = results.get("features")[0]["geometry"]["coordinates"]
        return geo.parse_location((lat, lon))
    except (KeyError, IndexError, RuntimeError):
        return None


def geocode(address, postcode=None, citycode=None, provider=None):
    # NOTE: if a provider is provided, we check the adress only on it, if no provider is provided we check first
    #       with BAN, and if the address is unknown we check with GEOPORTAIL, the provider used is returned.
    provider_provided = provider is not None
    provider = provider or Provider.BAN
    try:
        try:
            data = query({"q": address, "postcode": postcode, "citycode": citycode, "limit": 1}, provider=provider)
            data = data or {}
            if not data["features"]:
                data = {}
            if data and data["features"] and data["features"][0]["properties"]["score"] < 0.4:
                data = {}
        except RuntimeError:
            data = {}

        if not data and not provider_provided:
            return geocode(address, postcode, citycode, provider=Provider.GEOPORTAIL)

        if not data:
            return {}

        feature = data["features"][0]
        properties = feature["properties"]
        geometry = feature["geometry"]
        kind = properties["type"]
        if properties["score"] < 0.4:
            return {}

        voie = None
        lieu_dit = None
        if kind == "street":
            voie = properties.get("name")
        elif kind == "housenumber":
            voie = properties.get("street")
        elif kind == "locality":
            lieu_dit = properties.get("name")

        return {
            "geom": Point(geometry["coordinates"], srid=4326),
            "numero": properties.get("housenumber"),
            "voie": voie,
            "lieu_dit": lieu_dit,
            "code_postal": properties.get("postcode"),
            "commune": properties.get("city"),
            "code_insee": properties.get("citycode"),
            "provider": provider.value,  # FIXME Python3.11 drop this .value
        }
    except (KeyError, IndexError, TypeError) as err:
        raise RuntimeError(f"Erreur lors du géocodage de l'adresse {address}") from err


def query(params, timeout=8, provider=Provider.BAN):
    url = PROVIDER_URLS.get(provider)
    if not url:
        raise NotImplementedError(f"Geoloc provider with name {provider} not found")

    try:
        res = requests.get(url, params, timeout=timeout)
        logger.info(f"[{provider}] geocoding call: {res.url}")
        if res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la géolocalisation de l'adresse.")
        return res.json()
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        raise RuntimeError("Serveur de géocodage indisponible.")


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
