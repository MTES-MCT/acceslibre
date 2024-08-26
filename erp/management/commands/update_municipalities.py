import json

import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from erp.dataclasses import Municipality
from erp.models import Commune, Erp


class Command(BaseCommand):
    help = "Update all Commune objects based on official source"
    updated_insee = []

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _get_file(self):
        remote_url = "https://unpkg.com/@etalab/decoupage-administratif@latest/data/communes.json"
        local_file = "communes.json"
        data = requests.get(remote_url)
        with open(local_file, "wb") as file:
            file.write(data.content)

    def _get_details(self, insee_code):
        response = requests.get(f"https://geo.api.gouv.fr/communes/{insee_code}?fields=centre")
        return response.json()

    def _get_or_create_commune(self, data):
        try:
            commune = Commune.objects.get(code_insee=data.insee_code)
        except Commune.DoesNotExist:
            commune = Commune()
            json = self._get_details(data.insee_code)
            commune.geom = Point(json["centre"]["coordinates"][0], json["centre"]["coordinates"][1], srid=4326)
            print(f"Will create commune {data.name}")
        return commune

    def _make_obsolete(self, old_insee, new_insee):
        try:
            commune = Commune.objects.get(code_insee=old_insee)
        except Commune.DoesNotExist:
            return

        commune.obsolete = True

        if new_insee:
            erps = Erp.objects.filter(commune_ext=commune)
            if erps:
                new_commune = Commune.objects.get(code_insee=new_insee)
                if self.write:
                    erps.update(commune_ext=new_commune)
        if self.write:
            commune.save()

    def handle(self, *args, **options):
        self.write = options["write"]
        self._get_file()
        data = json.load(open("communes.json"))

        for municipality in data:
            validated_data = Municipality.from_json(municipality)

            if validated_data.type_of not in ("commune-actuelle", "commune-deleguee"):
                continue

            if validated_data.type_of == "commune-actuelle":
                if validated_data.postal_codes is None:
                    # Allowed in the file but not in our project
                    continue
                commune = self._get_or_create_commune(validated_data)
                commune.code_insee = validated_data.insee_code
                commune.nom = validated_data.name
                commune.departement = validated_data.departement
                commune.code_postaux = validated_data.postal_codes
                commune.population = validated_data.population
                commune.slug = None  # will be re-slugified on save()
                if self.write:
                    commune.save()
            elif validated_data.type_of == "commune-deleguee":
                self._make_obsolete(validated_data.insee_code, validated_data.parent_municipality)

            self.updated_insee.append(validated_data.insee_code)

        unknown_communes = Commune.objects.exclude(code_insee__in=self.updated_insee)
        print(f"Found {unknown_communes.count()} communes that were not found in the file")
        print(list(unknown_communes))
