import logging
import requests

from django.contrib.gis.geos import Point


logger = logging.getLogger(__name__)

GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"


def autocomplete(q, postcode=None, limit=5):
    params = {"q": q, "limit": limit, "autocomplete": 1}
    if postcode is not None:
        params["postcode"] = postcode
    data = query(params)
    return data.get("features") if data else None


def geocode(adresse):
    # retrieve geolocoder data
    try:
        data = query({"q": adresse, "limit": 1})
        feature = data["features"][0]
        # print(json.dumps(data, indent=2))
        properties = feature["properties"]
        type = properties["type"]
        # result type handling
        voie = None
        lieu_dit = None
        if type == "street":
            voie = properties.get("name")
        elif type == "housenumber":
            voie = properties.get("street")
        elif type == "locality":
            lieu_dit = properties.get("name")
        # score
        if properties["score"] < 0.5:
            return None
        # coordinates
        geometry = feature["geometry"]
        return {
            "geom": Point(geometry["coordinates"]),
            "numero": properties.get("housenumber"),
            "voie": voie,
            "lieu_dit": lieu_dit,
            "code_postal": properties.get("postcode"),
            "commune": properties.get("city"),
            "code_insee": properties.get("citycode"),
        }
    except (KeyError, IndexError, TypeError) as err:
        raise RuntimeError("Erreur lors du géocodage de l'adresse") from err


def query(params):
    try:
        res = requests.get(GEOCODER_URL, params)
        logger.info(f"Geocoder call: {res.url}")
        if res.status_code != 200:
            raise RuntimeError(
                f"Erreur HTTP {res.status_code} lors de la géolocalisation de l'adresse."
            )
        return res.json()
    except requests.exceptions.RequestException:
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
    return json[0] if len(json) > 0 else None
