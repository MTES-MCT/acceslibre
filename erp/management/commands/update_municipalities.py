from dataclasses import dataclass

import requests
from django.core.management.base import BaseCommand

from core.lib import geo
from erp.models import Commune, Erp

# TODO add tests
# - TODO add test will create new commune
# - TODO add test will update existing commune (check for contours)
# - TODO add test will make obsolete old commune without ERP
# - TODO add test will handle obsolete commune with ERP (still need to figure what to do)
# - TODO add test will skip gracefully missing data in API (code postal)
# TODO update contour
# TODO handle arrondissements

# class ContourSerializer(serializers.Serializer):
#     type = serializers.CharField
#     coordinates = serializers.ListField(
#         child=serializers.ListField(child=serializers.ListField(child=serializers.FloatField())))
#
# class MunicipalitySerializer(serializers.Serializer):
#     # TODO move me somewhere else ?
#     nom = serializers.CharField()
#     code = serializers.CharField(source="code_insee")
#     codeDepartement = serializers.CharField(source="departement")
#     codesPostaux = serializers.ListSerializer(child=serializers.CharField(), source="code_postaux")
#     population = serializers.IntegerField()
#     contour = ContourSerializer()


@dataclass
class Municipality:
    nom: str
    code_insee: str
    departement: str
    code_postaux: list
    population: int
    contour: str

    @classmethod
    def from_api(cls, json):
        return cls(
            nom=json["nom"],
            code_insee=json["code"],
            departement=json["codeDepartement"],
            code_postaux=json["codesPostaux"],
            population=json["population"],
            contour=json["contour"],
        )


class Command(BaseCommand):
    help = "Update all Commune objects based on official API"
    # TODO remove limit
    list_url = "https://geo.api.gouv.fr/communes/"
    updated_insee = []
    fields = ("nom", "code_insee", "departement", "code_postaux", "population")
    verbose = True  # TODO mainly here for debug / curiosity

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    # TODO remove me
    def _debug_commune_update(self, commune, validated_data):
        if not self.verbose:
            return

        for f in self.fields:
            if f == "population":
                continue
            if getattr(commune, f) != getattr(validated_data, f):
                print(
                    f"[{f}] Got {getattr(commune, f)} from DB and {getattr(validated_data,f)} from API for {commune} (insee: {validated_data.code_insee})"
                )

    def _get_or_create_commune(self, data):
        try:
            commune = Commune.objects.get(code_insee=data.code_insee)
            self._debug_commune_update(commune, data)
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

        if self.write:
            commune.save()
        self.updated_insee.append(commune.code_insee)

    def handle(self, *args, **options):
        self.write = options["write"]
        response = requests.get(self.list_url)
        response.raise_for_status()
        api_data = response.json()
        print(f"Found {len(api_data)} communes in API")

        insee_codes = [m["code"] for m in api_data]

        for insee_code in insee_codes:
            response = requests.get(
                f"https://geo.api.gouv.fr/communes/{insee_code}?fields=nom,code,codeDepartement,codesPostaux,population,contour"
            )
            response.raise_for_status()
            self._handle_api_data(response.json())

        unknown_communes = Commune.objects.exclude(code_insee__in=self.updated_insee)
        print(f"Found {unknown_communes.count()} communes that were not updated")
        print(unknown_communes)

        for unknown_commune in unknown_communes:
            has_erp = Erp.objects.filter(commune_ext=unknown_commune).exists()
            if has_erp:
                # TODO, example : La Neuville-Garnier (60)
                print(f"Don't know what to do in this case with commune {unknown_commune}")
            else:
                unknown_commune.obsolete = True
                if self.write:
                    unknown_commune.save()
