import csv

from django.core.management.base import BaseCommand

from core.mailer import BrevoMailer
from erp.models import Erp

NB_TO_MANAGE = 2


class Command(BaseCommand):
    help = "Import Brevo matching"

    def handle(self, *args, **options):
        nb_managed = 0
        with open("brevo.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for i, row in enumerate(reader):
                if not row["erp_slug"]:
                    continue
                print(f"~ Processing line {i}")
                try:
                    erp = Erp.objects.get(slug=row["erp_slug"])
                    assert not erp.import_email
                except Erp.DoesNotExist:
                    print(f"ERP with url {row.get('ERP_URL')}, slug={row['erp_slug']} not found. Ignoring the line...")
                    continue
                except AssertionError:
                    print(f"ERP with url {row.get('ERP_URL')}, import_email already set. Ignoring the line...")
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
