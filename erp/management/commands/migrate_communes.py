from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from erp.models import Commune, Erp


class Command(BaseCommand):
    help = "Assigne les communes aux ERP"

    def migrate_erp(self, erp):
        try:
            commune = Commune.objects.get(
                nom=erp.commune,
                departement=erp.code_postal[:2],
                # code_postaux__contains=[erp.code_postal],
            )
        except Commune.DoesNotExist:
            print(f"SKIP not found: {erp.commune} ({erp.code_postal[:2]})")
        except Commune.MultipleObjectsReturned:
            print(f"SKIP multiple: {erp.commune} ({erp.code_postal[:2]})")
        # else:
        #     print(f"PASS: {erp.nom}: {erp.commune} -> {commune.nom}")

    def handle(self, *args, **options):
        for erp in Erp.objects.all():
            self.migrate_erp(erp)
