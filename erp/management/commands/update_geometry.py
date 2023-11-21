import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from requests.exceptions import JSONDecodeError

from core.lib import geo
from erp.models import Commune


class Command(BaseCommand):
    help = "Update all contours and centers objects based on official API"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def handle(self, *args, **options):
        queryset = Commune.objects.filter(arrondissement=False, obsolete=False)

        for commune in queryset:
            insee_code = commune.code_insee
            response = requests.get(f"https://geo.api.gouv.fr/communes/{insee_code}?fields=contour,centre")

            try:
                json_data = response.json()
            except JSONDecodeError:
                print(f"Can't update {insee_code}, reponse : {response}")
                continue

            commune.contour = geo.geojson_mpoly(json_data["contour"])
            commune.geom = Point(
                json_data["centre"]["coordinates"][0],
                json_data["centre"]["coordinates"][1],
                srid=4326,
            )

            if options["write"]:
                commune.save()
