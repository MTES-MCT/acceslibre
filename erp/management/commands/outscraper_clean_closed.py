from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from outscraper import ApiClient

from erp.models import Erp


class Command(BaseCommand):
    help = "Check for closed ERPs from outscraper API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start_pk",
            type=int,
            required=False,
            default=0,
            help="Resume the check since this given ERP PK in our DB.",
        )
        parser.add_argument(
            "--write",
            default=False,
            action="store_true",
            help="Actually edit the database",
        )

        parser.add_argument(
            "--nb_days",
            type=int,
            required=False,
            default=60,
            help="Check the ERPs which have not been checked in the last nb_days.",
        )

    def _flag_erp_as_closed(self, existing_erp):
        print(f"Flag permanently closed ERP: {existing_erp}")
        if self.write:
            existing_erp.permanently_closed = True
            existing_erp.save()
        else:
            print("Dry run mode, no DB action, use --write to apply this deletion")

    def handle(self, *args, **options):
        self.write = options["write"]
        self.start_pk = options.get("start_pk")

        client = ApiClient(api_key=settings.OUTSCRAPER_API_KEY)

        limit_date = timezone.now() - timedelta(days=options["nb_days"])
        qs = Erp.objects.published().filter(Q(check_closed_at=None) | Q(check_closed_at__lte=limit_date))
        if self.start_pk:
            qs = qs.filter(pk__gte=self.start_pk)
        qs = qs.order_by("pk")

        for erp in qs.iterator():
            print(f"Checking ERP with PK {erp.pk}")
            query = f"{erp.numero} {erp.voie}" if erp.numero else erp.lieu_dit
            query = f"{erp.nom}, {query} {erp.code_postal} {erp.commune}"

            results = client.google_maps_search(query, limit=1, language="fr", region="FR", fields="business_status")[0]
            if results and results[0].get("business_status") == "CLOSED_PERMANENTLY":
                self._flag_erp_as_closed(erp)
                continue

            if self.write:
                erp.check_closed_at = timezone.now()
                erp.save(update_fields=("check_closed_at",))
