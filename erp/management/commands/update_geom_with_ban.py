from django.core.management.base import BaseCommand

from erp.models import Erp


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Démarrage CM ...")
        Erp.update_coordinates()
        print("Done.")
