from django.core.management.base import BaseCommand
from django.db.models import Q
from geopy import distance

from erp.duplicates import check_for_automatic_merge, find_main_erp_and_duplicates, merge_accessibility_with
from erp.exceptions import NeedsManualInspectionException, NotDuplicatesException
from erp.models import Erp

MAX_DISTANCE_FOR_DUPLICATE = 75
MAX_DISTANCE_FOR_DUPLICATE_WITH_CRITERIA = 500


class Command(BaseCommand):
    to_delete = 0
    for_manual_review = []
    unhandled = 0
    help = "Best effort to remove all the duplicates"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _get_duplicates(self, erp):
        duplicates = []
        qs = (
            Erp.objects.exclude(pk=erp.pk)
            .filter(nom__lower__in=(erp.nom.lower(), erp.nom.lower().replace("-", " ")))
            .filter(commune=erp.commune, published=True)
            .select_related("accessibilite")
            .exclude(accessibilite__isnull=True)
        )

        for potential_duplicate in qs:
            distance_diff = distance.distance(erp.geom, potential_duplicate.geom).m
            if distance_diff <= MAX_DISTANCE_FOR_DUPLICATE:
                duplicates.append(potential_duplicate.pk)
            elif MAX_DISTANCE_FOR_DUPLICATE < distance_diff <= MAX_DISTANCE_FOR_DUPLICATE_WITH_CRITERIA:
                try:
                    is_duplicate = check_for_automatic_merge([erp, potential_duplicate])
                    if is_duplicate:
                        duplicates.append(potential_duplicate.pk)
                except NeedsManualInspectionException:
                    message = f"{erp.pk};{potential_duplicate.pk};Need manual check for ERP {erp.nom} with {potential_duplicate.nom}"
                    self.for_manual_review.append(message)
                except NotDuplicatesException:
                    pass

        return Erp.objects.filter(pk__in=duplicates).select_related("accessibilite")

    def _keep_asp_id(self, erp, duplicates):
        ids = set([e.asp_id for e in duplicates if e.asp_id])
        if len(ids) == 1:
            erp.asp_id = list(ids)[0]
        elif ids:
            self.stderr.write(f"Can't find the correct ASP ID for {erp} with {duplicates}")
            self.stderr.write(f"Found possible ids {ids}")

    def _keep_street_number(self, erp, duplicates):
        numbers = set([e.numero for e in duplicates if e.asp_id])
        if len(numbers) == 1:
            erp.numero = list(numbers)[0]
        elif numbers:
            self.stderr.write(f"Can't find the correct Numero de voie for {erp} with {duplicates}")
            self.stderr.write(f"Found possible ids {numbers}")

    def _merge_and_delete(self, erp, duplicates):
        if len(duplicates) > 1:
            self.unhandled += len(duplicates)
            self.stderr.write(f"{len(duplicates)} ERPs found - Need to improve merge strategy in this case")
            return

        print("Merge and delete 1 ERP")
        if self.should_write:
            merge_accessibility_with(erp, duplicates[0])
            print(f"Will delete {duplicates[0]}")
            duplicates[0].delete()
        self.to_delete += 1

    def _has_a_permanently_closed(self, erps):
        return any([erp.permanently_closed for erp in erps])

    def handle(self, *args, **options):
        self.should_write = options["write"]
        queryset = Erp.objects.filter(Q(published=True) | Q(permanently_closed=True)).order_by("created_at")
        for erp in queryset.iterator():
            try:
                erp.refresh_from_db()
            except Erp.DoesNotExist:
                continue

            duplicates = self._get_duplicates(erp)
            if not duplicates:
                continue

            main_erp, duplicates = find_main_erp_and_duplicates([erp, *duplicates])
            if not duplicates:
                continue
            print(main_erp, duplicates)

            if self._has_a_permanently_closed([main_erp, *duplicates]):
                # Assuming we will delete all duplicates except the one flagged as permanently_closed
                self.to_delete += len(duplicates)
                if self.should_write:
                    print("One duplicate is permanently closed, all duplicates will deleted")
                    for erp in [main_erp, *duplicates]:
                        if erp.permanently_closed:
                            continue
                        erp.delete()

            self._keep_asp_id(main_erp, duplicates)
            self._keep_street_number(main_erp, duplicates)

            if main_erp.shares_same_accessibility_data_with(duplicates):
                self.to_delete += len(duplicates)
                if self.should_write:
                    print(f"Will delete {duplicates}")
                    for duplicate in duplicates:
                        duplicate.delete()
                    erp.save()
            else:
                self._merge_and_delete(erp, duplicates)
                if self.should_write:
                    erp.save()

        print(f"Will delete {self.to_delete}")
        print(f"Number of unhandled {self.unhandled}")
        print(f"Need manual review {len(self.for_manual_review)}")
        for line in self.for_manual_review:
            print(line)
