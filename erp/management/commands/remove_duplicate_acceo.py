from erp.models import Erp

from .base_duplication import BaseDuplicationCommand


class Command(BaseDuplicationCommand):
    to_delete = 0
    unhandled = 0
    help = "Best effort to remove all the duplicates that comes from the Service Public source."

    def _get_duplicates(self, erp):
        name_1 = erp.nom.lower()
        name_2 = erp.nom.lower().replace("mairie - ", "mairie de ")
        name_3 = erp.nom.lower().replace("mairie de ", "mairie - ")
        return (
            Erp.objects.exclude(pk=erp.pk)
            .filter(nom__lower__in=(name_1, name_2, name_3))
            .nearest(erp.geom, max_radius_km=0.500)
            .select_related("accessibilite")
            .exclude(accessibilite__isnull=True)
        )

    def _get_queryset(self):
        return (
            Erp.objects.filter(source=Erp.SOURCE_SERVICE_PUBLIC).select_related("accessibilite").order_by("created_at")
        )
