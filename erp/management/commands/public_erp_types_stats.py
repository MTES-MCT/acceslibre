import time
from pprint import pprint

from django.core.management.base import BaseCommand

from erp.provider import public_erp


class Command(BaseCommand):
    help = "Liste les types d'établissements possédant des entrées dans l'API des établissements publics"

    def handle(self, *args, **options):
        good = []
        final = {}
        for erp_type in public_erp.TYPES:
            try:
                res = public_erp.get(f"{public_erp.BASE_URL}/organismes/{erp_type}")
                count = len(res["features"][0])
                if count > 0:
                    good.append(erp_type)
                    print(f"PASS {erp_type} ({count})")
            except RuntimeError as err:
                print(f"SKIP error on {res.url}: {err}")
            time.sleep(0.02)
        if len(good) > 0:
            for erp_type in good:
                final[erp_type] = public_erp.TYPES[erp_type]
        print("Final dict:")
        pprint(final)
