import json
import requests

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon


from erp.models import Commune

# Standard (Polygon)
# https://geo.api.gouv.fr/communes/34120?fields=contour&format=json&geometry=contour
# Commune "trouée" (MultiPolygon)
# https://geo.api.gouv.fr/communes/2B049?fields=contour&format=json&geometry=contour


TEST_COMMUNES = (
    "34120",
    "2B049",
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for code in TEST_COMMUNES:
            commune = Commune.objects.get(code_insee=code)
            res = requests.get(
                f"https://geo.api.gouv.fr/communes/{code}?fields=contour&format=json&geometry=contour"
            )
            contour_str = json.dumps(res.json()["contour"])
            contour = GEOSGeometry(contour_str)
            try:
                if isinstance(contour, MultiPolygon):
                    pass
                elif isinstance(contour, Polygon):
                    contour = MultiPolygon([contour])
                else:
                    raise TypeError(f"{contour.contour_type} is not supported")
                commune.contour = contour
                commune.save()
                print(f"updated contour for {commune.nom}")

            except TypeError as e:
                print(e)
