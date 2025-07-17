import logging

import requests
from django.contrib.gis.geos import Point

from erp.provider.geocoder import GeolocRequester

logger = logging.getLogger(__name__)


class OSMRequester(GeolocRequester):
    provider: dict = None
    url = "https://nominatim.openstreetmap.org/search"

    def __init__(self, provider: dict) -> None:
        self.provider = provider

    def geocode(self, address, *args, **kwargs) -> dict:
        if not self.provider:
            raise Exception("Misconfigured")

        try:
            response = self.query({"q": address})
            if not response:
                return {}

            if not (features := response.get("features")):
                return {}

            feature = features[0]
            if feature.get("properties", {}).get("osm_type") != "node":
                return {}

            if (kind := feature.get("properties", {}).get("type")) not in ("house", "hamlet"):
                return {}

            voie = None
            lieu_dit = None
            geocoding = feature.get("properties")
            if kind in ("street", "house"):
                voie = geocoding.get("street")
            elif kind in ("hamlet", "locality"):
                lieu_dit = geocoding.get("name")

            geometry = feature["geometry"]
            return {
                "geom": Point(geometry["coordinates"], srid=4326),
                "numero": geocoding.get("housenumber"),
                "voie": voie,
                "lieu_dit": lieu_dit,
                "code_postal": geocoding.get("postcode"),
                "commune": geocoding.get("city"),
                "code_insee": "",
                "provider": self.provider["name"],
            }
        except (KeyError, IndexError, TypeError) as err:
            raise RuntimeError(f"Erreur lors du géocodage de l'adresse {address}") from err

    def query(self, params, timeout=8):
        response = requests.get(self.url, params | {"format": "geocodejson", "addressdetails": 1}, timeout=timeout)
        # logger.info(f"[{self.provider['name']}] geocoding call: {response.url}")

        if response.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {response.status_code} lors de la géolocalisation de l'adresse.")

        return response.json()
