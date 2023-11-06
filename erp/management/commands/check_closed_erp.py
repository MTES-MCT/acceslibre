# pip install googlemaps -> PipFile

import googlemaps
from django.conf import settings
from django.core.management.base import BaseCommand

from erp.models import Erp


class Command(BaseCommand):
    help = "Check for permanently closed ERPs."

    def handle(self, *args, **options):
        gmaps = googlemaps.Client(key=settings.PLACES_API_KEY)

        qs = Erp.objects.published().filter(pk__gte=20942).order_by("pk")[:1000]  # .iterator()
        for erp in qs:
            query = f"{erp.numero} {erp.voie}" if erp.numero else erp.lieu_dit
            query = f"{erp.nom}, {query} {erp.code_postal} {erp.commune}"
            result = gmaps.places(query)
            if len(results := result["results"]) != 1:
                # consider that we did not match the ERP
                continue
            if (status := results[0].get("business_status")) == "CLOSED_PERMANENTLY":
                print(f"ERP with pk {erp.pk} is {status}: {erp.get_absolute_uri()}")

        print(f"Last checked pk {erp.pk}")
