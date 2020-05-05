from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from erp.models import Commune, Erp


class Command(BaseCommand):
    help = "Assigne les communes aux ERP"

    def migrate_erp(self, erp):
        communes = Commune.objects.filter(
            Q(code_insee=erp.code_insee)
            | (Q(nom__iexact=erp.commune) & Q(departement=erp.code_postal[:2]))
            | Q(code_postaux__contains=[erp.code_postal])
        )
        if len(communes) == 0:
            print(f"SKIP not found: {erp.nom} à {erp.commune} ({erp.code_postal[:2]})")
        else:
            erp.commune_ext = communes[0]
            # erp.save()
            # print(f"PASS: {erp.nom}: {erp.commune} -> {communes[0].nom}")

    def handle(self, *args, **options):
        for erp in Erp.objects.all():
            self.migrate_erp(erp)
