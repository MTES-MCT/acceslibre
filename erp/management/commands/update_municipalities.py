import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from core.lib import geo
from erp.dataclasses import Municipality
from erp.models import Commune, Erp

# TODO add tests
# - TODO add test will handle obsolete commune with ERP (still need to figure what to do)
# - TODO add test will skip gracefully missing data in API (code postal)
# TODO run it for real once
# TODO handle arrondissements


class Command(BaseCommand):
    help = "Update all Commune objects based on official API"
    list_url = "https://geo.api.gouv.fr/communes/"
    updated_insee = []
    fields = ("nom", "code_insee", "departement", "code_postaux", "population")

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _get_or_create_commune(self, data):
        try:
            commune = Commune.objects.get(code_insee=data.code_insee)
        except Commune.DoesNotExist:
            commune = Commune()
            print(f"Will create commune {data}")
        return commune

    def _handle_api_data(self, api_data):
        validated_data = Municipality.from_api(api_data)
        commune = self._get_or_create_commune(validated_data)
        for f in self.fields:
            setattr(commune, f, getattr(validated_data, f))
        commune.contour = geo.geojson_mpoly(validated_data.contour)
        commune.geom = Point(
            validated_data.center_lon,
            validated_data.center_lat,
            srid=4326,
        )

        if self.write:
            commune.save()
        self.updated_insee.append(commune.code_insee)

    def handle(self, *args, **options):
        self.write = options["write"]
        response = requests.get(self.list_url)
        api_data = response.json()

        insee_codes = [m["code"] for m in api_data]

        for insee_code in insee_codes:
            response = requests.get(
                f"https://geo.api.gouv.fr/communes/{insee_code}?fields=nom,code,codeDepartement,codesPostaux,population,contour,centre"
            )
            self._handle_api_data(response.json())

        unknown_communes = Commune.objects.exclude(code_insee__in=self.updated_insee)
        print(f"Found {unknown_communes.count()} communes that were not updated")

        for unknown_commune in unknown_communes:
            has_erp = Erp.objects.filter(commune_ext=unknown_commune).exists()
            if has_erp:
                # TODO, example : La Neuville-Garnier (60)
                print(f"Don't know what to do in this case with commune {unknown_commune}")
            else:
                unknown_commune.obsolete = True
                if self.write:
                    unknown_commune.save()
