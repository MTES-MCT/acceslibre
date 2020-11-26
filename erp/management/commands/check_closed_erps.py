from django.core.management.base import BaseCommand

from erp.jobs import check_closed_erps


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            check_closed_erps.job(verbose=True)
        except KeyboardInterrupt:
            print("Interrompu.")
