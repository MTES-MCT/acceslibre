from django.core.management.base import BaseCommand, CommandError

from erp.models import Erp


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("Réindexation...")
        for erp in Erp.objects.all():
            erp.save()
        print("Réindexation effectuée.")
