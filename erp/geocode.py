import json
import requests

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"


def geocode(erp):
    # retrieve geolocoder data
    res = requests.get(GEOCODER_URL, {"q": erp.adresse, "limit": 1},)
    if res.status_code != 200:
        raise RuntimeError("Impossible de géocoder l'adresse.")
    data = res.json()
    try:
        feature = data["features"][0]
        # print(json.dumps(feature, indent=2))
        # score
        if feature["properties"]["score"] < 0.5:
            raise RuntimeError()
        # coordinates
        geometry = feature["geometry"]
        erp.geom = Point(geometry["coordinates"])
        # address

    except (KeyError, IndexError, RuntimeError) as err:
        # print(json.dumps(data, indent=2))
        erp.geom = None
        print(f"Failed geocoding address '{erp.adresse}': {err}")
    return erp
