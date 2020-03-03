import json
import requests

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"


def autocomplete(q, postcode=None, limit=5):
    params = {"q": q, "limit": limit, "autocomplete": 1}
    if postcode is not None:
        params["postcode"] = postcode
    data = query(params)
    return data["features"]


def geocode(adresse):
    # retrieve geolocoder data
    data = query({"q": adresse, "limit": 1})
    try:
        feature = data["features"][0]
        print(json.dumps(data, indent=2))
        properties = feature["properties"]
        # score
        if properties["score"] < 0.5:
            return None
        # coordinates
        geometry = feature["geometry"]
        return {
            "geom": Point(geometry["coordinates"]),
            "numero": properties.get("housenumber"),
            "voie": properties.get("street"),
            "lieu_dit": (
                properties.get("name")
                if properties.get("type") == "locality"
                else None
            ),
            "code_postal": properties.get("postcode"),
            "commune": properties.get("city"),
            "code_insee": properties.get("citycode"),
        }
    except (KeyError, IndexError, RuntimeError) as err:
        return None


def query(params):
    res = requests.get(GEOCODER_URL, params)
    if res.status_code != 200:
        raise RuntimeError("Serveur de géocodage indisponible.")
    return res.json()
