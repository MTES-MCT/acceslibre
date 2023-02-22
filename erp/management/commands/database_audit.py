from collections import defaultdict

from django.core.management.base import BaseCommand

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp


class Command(BaseCommand):
    def handle(self, *args, **options):
        query = Erp.objects.filter(published=True)
        nbs = defaultdict(int)
        for erp in query.iterator(chunk_size=200):
            try:
                if not erp.activite:
                    raise Exception("Missing activity")
                data = erp.__dict__
                data |= {"accessibilite": erp.accessibilite.__dict__}
                data |= {"activite": erp.activite.nom}
                serializer = ErpImportSerializer(instance=erp, data=data)
                serializer.is_valid(raise_exception=True)
                nbs["valid"] += 1
            except Exception as e:
                print(f"Erp id={erp.id} invalid, exception {e}")
                nbs["invalid"] += 1

        print(f"{nbs=}")
