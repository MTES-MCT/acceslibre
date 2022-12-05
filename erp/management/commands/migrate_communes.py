from django.core.management.base import BaseCommand
from django.db.models import Q

from erp.models import Commune, Erp


class Command(BaseCommand):
    help = "Assigne les communes aux ERP"

    def migrate_erp(self, erp):
        communes = Commune.objects.filter(
            Q(code_insee=erp.code_insee) | (Q(nom__unaccent=erp.commune) & Q(code_postaux__contains=[erp.code_postal]))
        )
        if len(communes) == 0:
            print(f"SKIP not found: {erp.nom} à {erp.commune} ({erp.code_postal[:2]})")

        else:
            erp.commune_ext = communes[0]
            if erp.commune_ext.nom != erp.commune:
                print(f"Warning: {erp.commune_ext.nom} != {erp.commune}")
            erp.save()
            print(f"OK: {erp.nom}: {erp.commune} -> {communes[0].nom}")

    def handle(self, *args, **options):
        for erp in Erp.objects.filter(commune_ext__isnull=True):
            self.migrate_erp(erp)
