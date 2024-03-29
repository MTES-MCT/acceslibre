from import_export import resources

from .models import Erp
from .schema import get_a11y_fields

VILLES_CIBLES = ["rueil-malmaison", "courbevoie", "lorient"]

accessibility_fields = [f"accessibilite__{fieldname}" for fieldname in get_a11y_fields()]


class ErpAdminResource(resources.ModelResource):
    class Meta:
        model = Erp
        skip_unchanged = True
        fields = [
            "nom",
            "published",
            "geom",
            "accessibilite",
            "user",
            "user_type",
            "source",
            "created_at",
            "updated_at",
        ] + accessibility_fields


class ErpResource(resources.ModelResource):
    class Meta:
        model = Erp
        skip_unchanged = True
        exclude = (
            "id",
            "telephone",
            "site_internet",
            "created_at",
            "updated_at",
        )

    def handle_5digits_code(self, cpost):
        cpost = str(cpost)
        if len(cpost) == 4:
            return "0" + cpost
        return cpost

    def skip_row(self, instance, original):
        if any(
            [
                instance.nom.strip() == "",
                instance.code_postal.strip() == "",
                instance.commune.strip() == "",
                instance.voie.strip() == "" and instance.lieu_dit.strip() == "",
                instance.commune.lower().strip() not in VILLES_CIBLES,
                instance.geom is None,
            ]
        ):
            return True
        return super(ErpResource, self).skip_row(instance, original)
