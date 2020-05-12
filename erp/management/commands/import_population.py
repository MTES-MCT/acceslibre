import sys
import time

from django.core.management.base import BaseCommand, CommandError

from erp.models import Commune
from erp.geocoder import geocode_commune


class SkipImport(Exception):
    pass


class Command(BaseCommand):
    help = "Importe les données de population des communes de France"

    def import_commune(self, commune):
        data = geocode_commune(commune.code_insee)
        time.sleep(0.02)
        if not data or "population" not in data:
            raise SkipImport()
        commune.population = data["population"]
        commune.save()
        print(f"{commune}: {commune.population}")

    def handle(self, *args, **options):
        for commune in Commune.objects.all():
            try:
                self.import_commune(commune)
            except SkipImport as err:
                sys.stdout.write("S")
                sys.stdout.flush()
            else:
                sys.stdout.write(".")
                sys.stdout.flush()

        print("Mise à jour effectuée.")
