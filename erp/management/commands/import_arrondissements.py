import json
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from core.lib import geo, text
from erp.models import Commune


class Command(BaseCommand):
    """Import arrondissement data into the Commune db table.

    Data source: https://public.opendatasoft.com/explore/dataset/arrondissements-millesimes0/export/
    """

    def handle(self, *args, **options):
        json_file_path = os.path.join(settings.BASE_DIR, "data", "arrondissements.json")
        with open(json_file_path) as json_file:
            contents = json.load(json_file)
            for feature in contents["features"]:
                props = feature["properties"]
                code_postal = f"{str(props['code_dpartement'])}"
                if props["nom_com"].startswith("LYON"):
                    code_postal += f"00{props['code_insee'][4:]}"
                else:
                    code_postal += f"0{props['code_insee'][3:]}"
                commune = Commune(
                    arrondissement=True,
                    nom=self._format_nom(props["nom_com"]),
                    departement=str(props["code_dpartement"]),
                    code_insee=props["code_insee"],
                    geom=Point(props["geo_point"]),
                    contour=geo.geojson_mpoly(feature["geometry"]),
                    population=props["population"],
                    superficie=props["superficie"],
                    code_postaux=[code_postal],
                )
                print(f"Imported {commune.nom} {commune.code_insee}")
                commune.save()

    def _format_nom(self, nom):
        parts = [p for p in nom.lower().split("-")]
        return text.ucfirst(" ".join(parts))
