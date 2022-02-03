from erp.models import Erp
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Démarrage CM ...")
        Erp.update_coordinates()
        print("Done.")
