import csv

from django.core.management.base import BaseCommand

from core.mailer import BrevoMailer
from erp.models import Erp

NB_TO_MANAGE = 2


class Command(BaseCommand):
    help = "Import Brevo matching"

    @staticmethod
    def _get_slug_from_url(url):
        return url.split("/")[-2]

    def handle(self, *args, **options):
        nb_managed = 0
        with open("brevo_debug.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for i, row in enumerate(reader):
                if not row["ERP_URL"]:
                    continue
                print(f"~ Processing line {i}")
                try:
                    slug = self._get_slug_from_url(row["ERP_URL"])
                    erp = Erp.objects.get(slug=slug)
                    assert not erp.import_email
                except (Erp.DoesNotExist, AssertionError):
                    print(f"ERP with url {row['ERP_URL']}, slug={slug} not found. Ignoring the line...")
                    continue

                erp.import_email = row["EMAIL"]
                erp.save()

                nb_managed += 1

                BrevoMailer().sync_erp(erp)
                BrevoMailer().send_email(
                    to_list=erp.import_email,
                    template="erp_imported_brevo_matching",
                    context={"erp_url": erp.get_absolute_uri()},
                )
                print(f"Done for {erp.nom}")
                if nb_managed >= NB_TO_MANAGE:
                    print("Done, nb_managed >= NB_TO_MANAGE")
                    break
