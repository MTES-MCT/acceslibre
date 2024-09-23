from django.core.management.base import BaseCommand

from django.contrib.gis.gdal import DataSource

from core.lib import geo
from erp.models import Departement


class Command(BaseCommand):
    help = "Créé les contours pour les département"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin du fichier à traiter",
        )

    def handle(self, *args, **options):
        self.stdout.write("Démarrage de l'importation")
        data_source = DataSource(options["file"])

        for feature in data_source[0]:
            contour = geo.geojson_mpoly(feature.geom.json)
            Departement.objects.create(code=feature.get("code_insee"), contour=contour)
