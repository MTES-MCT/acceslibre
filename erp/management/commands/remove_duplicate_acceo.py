from geopy import distance

from erp.models import Erp

from .base_duplication import BaseDuplicationCommand


class Command(BaseDuplicationCommand):
    to_delete = 0
    unhandled = 0
    help = "Best effort to remove all the duplicates that comes from the Acceo source."

    def _get_duplicates(self, erp):
        qs = (
            Erp.objects.exclude(pk=erp.pk)
            .filter(nom__lower=erp.nom.lower())
            .filter(commune=erp.commune, published=True)
            .select_related("accessibilite")
            .exclude(accessibilite__isnull=True)
        )
        duplicates = []
        for potential_duplicate in qs:
            distance_diff = distance.distance(
                (erp.geom.y, erp.geom.x), (potential_duplicate.geom.y, potential_duplicate.geom.x)
            ).m
            if distance_diff <= 70:
                duplicates.append(potential_duplicate.pk)

        return Erp.objects.filter(pk__in=duplicates)

    def _get_queryset(self):
        return (
            Erp.objects.filter(source=Erp.SOURCE_ACCEO, published=True)
            .select_related("accessibilite")
            .order_by("created_at")
        )
