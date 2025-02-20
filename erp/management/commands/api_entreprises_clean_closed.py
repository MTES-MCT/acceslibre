from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from erp.models import Activite, Erp
from erp.provider.entreprise import check_closed

IGNORED_ACTIVITIES = ["Administration publique", "Mairie", "Gendarmerie", "Bureau de poste"]


class Command(BaseCommand):
    help = "Check for closed ERPs from API Entreprises"

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
        print(f"Flag permanently closed ERP: {existing_erp} - {existing_erp.get_absolute_uri()}")
        if not self.write:
            print("Dry run mode, no DB action, use --write to apply this deletion")
            return

        existing_erp.permanently_closed = True
        existing_erp.save()

    def handle(self, *args, **options):
        self.write = options["write"]
        self.start_pk = options.get("start_pk")

        ignored_activities = Activite.objects.filter(nom__in=IGNORED_ACTIVITIES)
        if ignored_activities.count() != len(IGNORED_ACTIVITIES):
            print("Please check the IGNORED_ACTIVITIES list, at least one activity has not been found. Exit...")
            return

        limit_date = timezone.now() - timedelta(days=options["nb_days"])
        qs = Erp.objects.published().filter(Q(check_closed_at=None) | Q(check_closed_at__lte=limit_date))
        qs = qs.exclude(activite__in=ignored_activities)
        if self.start_pk:
            qs = qs.filter(pk__gte=self.start_pk)
        qs = qs.order_by("pk")

        for erp in qs.iterator():
            print(f"Checking ERP with PK {erp.pk}")
            query = f"{erp.numero} {erp.voie}" if erp.numero else erp.lieu_dit
            query = f"{erp.nom}, {query} {erp.code_postal} {erp.commune}"

            query_address = f"{erp.numero} {erp.voie}" if erp.numero else erp.lieu_dit
            query_address = f"{query_address} {erp.code_postal} {erp.commune}"
            if check_closed(erp.nom, query_address, erp.commune_ext.code_insee):
                self._flag_erp_as_closed(erp)
                continue

            if self.write:
                erp.check_closed_at = timezone.now()
                erp.save(update_fields=("check_closed_at",))
