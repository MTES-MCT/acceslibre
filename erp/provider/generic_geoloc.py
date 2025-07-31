import logging

import requests
from django.contrib.gis.geos import Point

logger = logging.getLogger(__name__)


class GeolocRequester:
    provider: dict = None

    urls = {
        "ban": "https://api-adresse.data.gouv.fr/search/",
        "geoportail": "https://wxs.ign.fr/essentiels/geoportail/geocodage/rest/0.1/search",
    }

    def __init__(self, provider: dict) -> None:
        self.provider = provider

    def geocode(self, address, postcode=None, citycode=None) -> dict:
        if not self.provider:
            raise Exception("Misconfigured")

        try:
            try:
                data = self.query(
                    {"q": address, "postcode": postcode, "citycode": citycode, "limit": 1, "autocomplete": 0}
                )
            except RuntimeError:
                return {}

            if not data or not data["features"]:
                return {}

            if data["features"][0]["properties"]["score"] < 0.4:
                return {}

            feature = data["features"][0]
            properties = feature["properties"]
            geometry = feature["geometry"]
            kind = properties["type"]

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
                "provider": self.provider["name"],
                "ban_id": properties.get("id"),
            }
        except (KeyError, IndexError, TypeError) as err:
            raise RuntimeError(f"Erreur lors du géocodage de l'adresse {address}") from err

    def query(self, params, timeout=8):
        url = self.urls.get(self.provider["name"])
        if not url:
            raise Exception("Misconfigured")

        try:
            res = requests.get(url, params, timeout=timeout)
            # logger.info(f"[{self.provider['name']}] geocoding call: {res.url}")
            if res.status_code != 200:
                raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la géolocalisation de l'adresse.")
            return res.json()
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            raise RuntimeError("Serveur de géocodage indisponible.")
