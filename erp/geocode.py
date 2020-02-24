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


def geocode(erp):
    # retrieve geolocoder data
    data = query({"q": erp.adresse, "limit": 1})
    try:
        feature = data["features"][0]
        # print(json.dumps(feature, indent=2))
        # score
        if feature["properties"]["score"] < 0.5:
            raise RuntimeError()
        # coordinates
        geometry = feature["geometry"]
        erp.geom = Point(geometry["coordinates"])
    except (KeyError, IndexError, RuntimeError) as err:
        # print(json.dumps(data, indent=2))
        erp.geom = None
        print(f"Failed geocoding address '{erp.adresse}': {err}")
    return erp


def query(params):
    res = requests.get(GEOCODER_URL, params)
    if res.status_code != 200:
        raise RuntimeError("Impossible de géocoder l'adresse.")
    return res.json()
