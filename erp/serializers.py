import base64
import json
import logging

from django.contrib.gis.geos import Point
from django.contrib.gis.serializers import geojson


logger = logging.getLogger(__name__)


class SpecialErpSerializer(geojson.Serializer):
    # see https://stackoverflow.com/a/56557206/330911

    def end_object(self, obj):  # noqa
        for field in self.selected_fields:
            if field == "pk":
                continue
            elif field in self._current.keys():
                continue
            elif field == "absolute_url":
                self._current[field] = obj.get_absolute_url()
            elif field == "adresse":
                self._current[field] = obj.adresse
            elif field == "has_accessibilite":
                self._current[field] = obj.has_accessibilite()
            else:
                try:
                    if "__" in field:
                        fields = field.split("__")
                        value = obj
                        for f in fields:
                            value = getattr(value, f)
                        if value != obj:
                            self._current[field] = value
                except AttributeError:
                    pass
        super().end_object(obj)


def decode_provider_data(data):
    try:
        decoded = json.loads(base64.urlsafe_b64decode(data).decode())
        if "coordonnees" in decoded:
            decoded["geom"] = Point(decoded["coordonnees"])
        return decoded
    except Exception as err:
        logger.error(f"decode_provider_data error: {err}")
        raise RuntimeError(
            "Impossible de décoder les informations du fournisseur de données"
        )


def encode_provider_data(data):
    try:
        if "exists" in data:
            del data["exists"]
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode("utf-8")
    except Exception as err:
        logger.error(f"encode_provider_data error: {err}")
        raise RuntimeError(
            "Impossible d'encoder les informations du fournisseur de données"
        )
