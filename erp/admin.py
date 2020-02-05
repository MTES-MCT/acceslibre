import nested_admin
import re

from datetime import datetime
from django import forms
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.core.exceptions import ValidationError
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Activite,
    Erp,
    Label,
    Accessibilite,
    Cheminement,
    EquipementMalentendant,
)
from .geocode import geocode

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
        row["addresse"] = " ".join(
            [
                row["num"],
                row["cplt"],
                row["voie"],
                row["lieu_dit"],
                row["cpost"],
                row["commune"],
            ]
        ).strip()
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


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)


@admin.register(EquipementMalentendant)
class EquipementMalentendantAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)


class CheminementInline(nested_admin.NestedStackedInline):
    model = Cheminement
    max_num = 6
    extra = 0
    fields = (
        "type",
        "pente",
        "devers",
        "reperage_vitres",
        "bande_guidage",
        "guidage_sonore",
        "largeur_mini",
        "rampe",
        "aide_humaine",
        "escalier_marches",
        "escalier_reperage",
        "escalier_main_courante",
        "ascenseur",
    )


class AccessibiliteInline(nested_admin.NestedStackedInline):
    model = Accessibilite
    inlines = [CheminementInline]
    fieldsets = [
        (
            "Stationnement",
            {
                "fields": [
                    "stationnement_presence",
                    "stationnement_pmr",
                    "stationnement_ext_presence",
                    "stationnement_ext_pmr",
                ]
            },
        ),
        (
            "Entrée",
            {
                "fields": [
                    "entree_reperage",
                    "entree_interphone",
                    "entree_pmr",
                    "entree_pmr_informations",
                    "reperage_vitres",
                    "guidage_sonore",
                    "largeur_mini",
                    "rampe",
                    "aide_humaine",
                    "escalier_marches",
                    "escalier_reperage",
                    "escalier_main_courante",
                    "ascenseur",
                ]
            },
        ),
        (
            "Accueil",
            {
                "fields": [
                    "accueil_visibilite",
                    "accueil_personnels",
                    "accueil_equipements_malentendants",
                    "accueil_prestations",
                ]
            },
        ),
        (
            "Sanitaires",
            {"fields": ["sanitaires_presence", "sanitaires_adaptes"]},
        ),
        ("Labels", {"fields": ["labels"]}),
    ]


class ErpAdminForm(forms.ModelForm):
    class Meta:
        model = Erp
        fields = ("activite",)

    activite = forms.ModelChoiceField(
        queryset=Activite.objects.order_by("nom"),
        required=False,
        empty_label="Inconnue",
    )


@admin.register(Erp)
class ErpAdmin(
    ImportExportModelAdmin, OSMGeoAdmin, nested_admin.NestedModelAdmin
):
    form = ErpAdminForm
    resource_class = ErpResource

    inlines = [AccessibiliteInline]
    list_display = (
        "nom",
        "activite",
        "code_postal",
        "commune",
        "renseignee",
        "updated_at",
    )
    list_display_links = ("nom",)
    list_filter = [
        ("activite", RelatedDropdownFilter),
        "created_at",
        "updated_at",
    ]
    point_zoom = 18
    map_height = 300
    save_on_top = True
    search_fields = ["nom", "activite__nom", "code_postal", "commune"]
    scrollable = False
    sortable_by = ("nom", "activite__nom", "code_postal", "commune")
    view_on_site = False

    fieldsets = [
        (None, {"fields": ["activite", "nom", "siret"]}),
        ("Contact", {"fields": ["telephone", "site_internet"]}),
        (
            "Localisation",
            {
                "fields": [
                    "numero",
                    "voie",
                    "lieu_dit",
                    "code_postal",
                    "commune",
                    "code_insee",
                    "geom",
                ]
            },
        ),
    ]

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            # hide geom when object is new
            fieldsets = dict(self.fieldsets.copy())
            fieldsets["Localisation"]["fields"] = [
                f for f in fieldsets["Localisation"]["fields"] if f != "geom"
            ]
            new_fieldsets = list(fieldsets.items())
            self.fieldsets = new_fieldsets
        return self.fieldsets

    def renseignee(self, instance):
        return instance.accessibilite is not None

    renseignee.boolean = True
    renseignee.short_description = "Renseignée"

    def save_model(self, request, obj, form, change):
        localized_obj = geocode(obj)
        super(ErpAdmin, self).save_model(request, localized_obj, form, change)


# General admin heading & labels
admin.site.site_title = "Access4all admin"
admin.site.site_header = "Access4all admin"
admin.site.index_title = "Access4all administration"
