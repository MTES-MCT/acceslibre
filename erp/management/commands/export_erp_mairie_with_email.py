import csv
import os
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand

from erp.models import Erp


class Command(BaseCommand):
    help = "Exporte les ERPs avec l'activité Mairie ayant un contact_email non vide."

    def handle(self, *args, **options):
        erps = Erp.objects.filter(activite__nom="Mairie", contact_email__isnull=False)
        stamp = date.today().isoformat()
        csv_filename = f"export-mairie-{stamp}.csv"
        with open(os.path.join(settings.BASE_DIR, csv_filename), "w") as csvfile:
            fieldnames = [
                "contact_email",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for erp in erps:
                writer.writerow(
                    {
                        "contact_email": erp.contact_email.lower(),
                    }
                )
