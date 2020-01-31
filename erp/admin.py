import re

from datetime import datetime
from django.contrib import admin
from django.core.exceptions import ValidationError
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Erp

CCONFORME_DATE_FORMAT = "%Y%m%d"
CCONFORME_GEOM_RE = re.compile(r"POINT\((\d+\.\d+) (\d+\.\d+)\)")


class ErpResource(resources.ModelResource):
    class Meta:
        model = Erp
        # skip_unchanged = True
        exclude = ("id",)

    def before_import_row(self, row, **kwargs):
        # date field
        try:
            row["date"] = datetime.strptime(row["date"], CCONFORME_DATE_FORMAT)
        except (AttributeError, ValueError):
            return  # TODO: warning/info
        # adresse
        row["addresse"] = " ".join([row["num"], row["cplt"], row["voie"], row["lieu_dit"], row["cpost"], row["commune"]]).strip()
        # lat & lon fields
        try:
            (slat, slon) = CCONFORME_GEOM_RE.match(row["geom"]).groups()
            (lat, lon) = (float(slat), float(slon))
        except (AttributeError, ValueError):
            return  # TODO: warning/info
        row["lat"] = lat
        row["lon"] = lon
        # cplt
        if row["cplt"] == "NR":
            row["cplt"] = ""
        # categorie
        try:
            int(row["categorie"])
        except ValueError:
            row["categorie"] = ""
        # precision
        try:
            float(row["precision"])
        except ValueError:
            row["precision"] = ""
        # nature
        row["nature"].strip().upper()

    def skip_row(self, instance, original):
        if instance.lat is None or instance.lon is None:
            return True
        return super(ErpResource, self).skip_row(instance, original)


class ErpAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = ErpResource

    list_display = ("nom", "nature", "domaine", "dossier", "cpost", "commune")
    list_display_links = ("nom",)
    list_filter = ("nature", "dossier", "categorie", "domaine")
    save_on_top = True
    search_fields = ["nom", "domaine"]
    sortable_by = ("nom", "cpost", "commune")
    view_on_site = False

    fieldsets = [
        (None, {"fields": ["domaine", "nom", "dossier", "nature", "categorie", "siret"]}),
        (
            "Localisation",
            {"fields": ["adresse", "lat", "lon", "num", "cplt", "voie", "lieu_dit", "cpost", "commune", "code_insee"]},
        ),
        ("Autorisation", {"fields": ["demandeur", "id_adap"]}),
        ("Attestation", {"fields": ["date", "duree"]}),
        ("Dérogation", {"fields": ["derog", "objet_dero", "precision", "qualite"]}),
        ("SDIS", {"fields": ["type"]}),
    ]


admin.site.register(Erp, ErpAdmin)
