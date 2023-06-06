from rest_framework_gis.filters import InBBoxFilter


class ZoneFilter(InBBoxFilter):
    bbox_param = "zone"

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.bbox_param,
                "required": False,
                "in": "query",
                "description": "Coordonnées du cadre englobant la recherche au format `min_longitude,min_latitude,max_longitude,max_latitude` (par ex. ?zone=4.849022,44.885530,4.982661,44.963994)",
                "schema": {
                    "type": "array",
                    "items": {"type": "float"},
                    "minItems": 4,
                    "maxItems": 4,
                    "example": [-180, -90, 180, 90],
                },
                "style": "form",
                "explode": False,
            },
        ]
