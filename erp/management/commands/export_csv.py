from django.core.management.base import BaseCommand

from erp.jobs import export_to_datagouv


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            export_to_datagouv.job()
        except KeyboardInterrupt:
            print("Interrompu.")
