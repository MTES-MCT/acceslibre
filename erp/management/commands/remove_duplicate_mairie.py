from django.core.management.base import BaseCommand
from geopy import distance

from erp.exceptions import MergeException, MultipleAspIdForDuplicates
from erp.models import Erp


class Command(BaseCommand):
    to_delete = 0
    unhandled = 0
    help = "Best effort to remove all the duplicates for town halls."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--write",
            action="store_true",
            help="Actually edit the database",
        )

    def _get_duplicates(self, erp):
        name_1 = erp.nom.lower()
        name_2 = erp.nom.lower().replace("mairie - ", "mairie de ")
        name_3 = erp.nom.lower().replace("mairie de ", "mairie - ")
        qs = (
            Erp.objects.exclude(pk=erp.pk)
            .filter(nom__lower__in=(name_1, name_2, name_3))
            .filter(commune=erp.commune, published=True)
            .select_related("accessibilite")
            .exclude(accessibilite__isnull=True)
        )
        duplicates = []
        for potential_duplicate in qs:
            distance_diff = distance.distance(
                (erp.geom.y, erp.geom.x), (potential_duplicate.geom.y, potential_duplicate.geom.x)
            ).m
            if distance_diff <= 500:
                duplicates.append(potential_duplicate.pk)

        return Erp.objects.filter(pk__in=duplicates)

    def _delete_duplicates(self, duplicates):
        self.to_delete += len(duplicates)
        if self.should_write:
            print(f"Will delete {duplicates}")
            duplicates.delete()

    def _merge_and_delete(self, erp, duplicates):
        if duplicates.count() > 1:
            self.unhandled += duplicates.count()
            self.stderr.write(f"{duplicates.count()} ERPs found - Need to improve merge strategy in this case")
            return

        print("Merge and delete 1 ERP")
        if self.should_write:
            erp.merge_accessibility_with(duplicates[0])
            print(f"Will delete {duplicates[0]}")
            duplicates[0].delete()
        self.to_delete += 1

    def _get_asp_id(self, duplicates):
        ids = set([e.asp_id for e in duplicates if e.asp_id])
        if len(ids) == 1:
            return list(ids)[0]
        if len(ids) > 1:
            raise MultipleAspIdForDuplicates

    def handle(self, *args, **options):
        self.should_write = options["write"]
        print(f"Starts with {Erp.objects.count()} ERPs")
        queryset = (
            Erp.objects.filter(nom__icontains="Mairie ", published=True)
            .select_related("accessibilite")
            .order_by("created_at")
        )

        for erp in queryset.iterator():
            try:
                erp.refresh_from_db()
            except Erp.DoesNotExist:
                continue

            duplicates = self._get_duplicates(erp)
            if not duplicates:
                continue

            print(erp, duplicates)
            if erp.shares_same_accessibility_data_with(duplicates):
                try:
                    asp_id = self._get_asp_id(duplicates)
                    self._delete_duplicates(duplicates)
                    if asp_id:
                        erp.asp_id = asp_id
                        erp.save()
                except MultipleAspIdForDuplicates:
                    self.stderr.write(f"Can't find the correct ASP ID for {duplicates}")
            else:
                try:
                    asp_id = self._get_asp_id(duplicates)
                    self._merge_and_delete(erp, duplicates)
                    if asp_id:
                        erp.asp_id = asp_id
                        erp.save()
                except MultipleAspIdForDuplicates:
                    self.stderr.write(f"Can't find the correct ASP ID for {duplicates}")
                except MergeException:
                    pass

        print(f"Has deleted {self.to_delete} ERPs")
        print(f"Unhandled cases : {self.unhandled} (triple merge or more)")
        print(f"End with {Erp.objects.count()} ERPs")
