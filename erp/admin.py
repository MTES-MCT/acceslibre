import nested_admin

from datetime import datetime
from django import forms
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.gis.admin import OSMGeoAdmin
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from import_export.admin import ImportExportModelAdmin

from .forms import AdminAccessibiliteForm, AdminErpForm, AdminCheminementForm
from .imports import ErpResource
from .models import (
    Activite,
    Erp,
    Label,
    Accessibilite,
    Cheminement,
    EquipementMalentendant,
)


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("nom", "erp_count", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(_erp_count=Count("erp", distinct=True),)
        return queryset

    def erp_count(self, obj):
        return obj._erp_count


@admin.register(EquipementMalentendant)
class EquipementMalentendantAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom",)


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom",)


class CheminementInline(nested_admin.NestedStackedInline):
    model = Cheminement
    form = AdminCheminementForm
    classes = ("collapse",)
    max_num = 5
    extra = 0
    fields = (
        "type",
        "nom",
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
    class Media:
        css = {"all": ("admin/a4a-addons.css",)}

    model = Accessibilite
    form = AdminAccessibiliteForm
    autocomplete_fields = ["accueil_equipements_malentendants", "labels"]
    inlines = [CheminementInline]
    fieldsets = [
        (
            "Stationnement",
            {
                "classes": ("collapse",),
                "fields": [
                    "stationnement_presence",
                    "stationnement_pmr",
                    "stationnement_ext_presence",
                    "stationnement_ext_pmr",
                ],
            },
        ),
        (
            "Entrée",
            {
                "classes": ("collapse",),
                "fields": [
                    "entree_plain_pied",
                    "entree_reperage",
                    "entree_interphone",
                    "entree_pmr",
                    "entree_pmr_informations",
                    "reperage_vitres",
                    "guidage_sonore",
                    "largeur_mini",
                    "rampe",
                    "aide_humaine",
                    "ascenseur",
                    "escalier_marches",
                    "escalier_reperage",
                    "escalier_main_courante",
                ],
            },
        ),
        (
            "Accueil",
            {
                "classes": ("collapse",),
                "fields": [
                    "accueil_visibilite",
                    "accueil_personnels",
                    "accueil_equipements_malentendants",
                    "accueil_prestations",
                ],
            },
        ),
        (
            "Sanitaires",
            {
                "classes": ("collapse",),
                "fields": ["sanitaires_presence", "sanitaires_adaptes"],
            },
        ),
        ("Labels", {"classes": ("collapse",), "fields": ["labels"]}),
    ]

    def get_formset(self, request, obj=None, **kwargs):
        # see https://stackoverflow.com/a/37558444/330911
        formset = super(AccessibiliteInline, self).get_formset(
            request, obj, **kwargs
        )
        form = formset.form
        if "accueil_equipements_malentendants" in form.base_fields:
            widget = form.base_fields[
                "accueil_equipements_malentendants"
            ].widget
            widget.can_add_related = False
            widget.can_change_related = False
            widget.can_delete_related = False
        if "labels" in form.base_fields:
            form.base_fields["labels"].widget.can_add_related = False
            form.base_fields["labels"].widget.can_change_related = False
            form.base_fields["labels"].widget.can_delete_related = False
        return formset


class CommuneFilter(admin.SimpleListFilter):
    # see https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    title = "Commune"
    parameter_name = "commune"

    def lookups(self, request, model_admin):
        values = Erp.objects.order_by("commune").distinct("commune")
        return ((v.commune, v.commune) for v in values)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(commune=self.value())


@admin.register(Erp)
class ErpAdmin(OSMGeoAdmin, nested_admin.NestedModelAdmin):
    class Media:
        css = {"all": ("admin/a4a-addons.css",)}

    # note: add ImportExportModelAdmin as a first mixin to handle imports/exports
    # resource_class = ErpResource
    form = AdminErpForm

    actions = ["assign_activite", "publish", "unpublish"]
    inlines = [AccessibiliteInline]
    list_display = (
        "nom",
        "activite",
        "voie_ou_lieu_dit",
        "code_postal",
        "commune",
        "published",
        "geolocalise",
        "renseignee",
        "user",
        "updated_at",
        "view_search",
        "view_link",
    )
    list_select_related = ("activite", "accessibilite", "user")
    list_display_links = ("nom",)
    list_per_page = 20
    list_filter = [
        ("activite", RelatedDropdownFilter),
        ("user", RelatedDropdownFilter),
        CommuneFilter,
        "created_at",
        "updated_at",
    ]
    point_zoom = 18
    map_height = 300
    save_on_top = True
    search_fields = ["nom", "activite__nom", "code_postal", "commune"]
    autocomplete_fields = ["activite"]
    scrollable = False
    sortable_by = ("nom", "activite__nom", "code_postal", "commune")
    view_on_site = True

    fieldsets = [
        (None, {"fields": ["activite", "nom", "siret", "published"]}),
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

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def assign_activite(self, request, queryset):
        if "apply" in request.POST:
            try:
                queryset.update(activite_id=int(request.POST["activite"]))
                self.message_user(
                    request, f"{queryset.count()} ERP ont été modifiés."
                )
            except (KeyError, TypeError):
                pass
            return HttpResponseRedirect(request.get_full_path())

        return render(
            request,
            "admin/assign_activite.html",
            context={"erps": queryset, "activites": Activite.objects.all()},
        )

    assign_activite.short_description = "Assigner une nouvelle catégorie"

    def publish(self, request, queryset):
        queryset.update(published=True)

    publish.short_description = "Publier"

    def unpublish(self, request, queryset):
        queryset.update(published=False)

    unpublish.short_description = "Mettre hors ligne"

    def get_form(self, request, obj=None, **kwargs):
        # see https://code.djangoproject.com/ticket/9071#comment:24
        form = super(ErpAdmin, self).get_form(request, obj, **kwargs)
        if "activite" in form.base_fields:
            form.base_fields["activite"].widget.can_add_related = False
            form.base_fields["activite"].widget.can_change_related = False
            form.base_fields["activite"].widget.can_delete_related = False
        # hide geom field on new obj
        if "geom" in form.base_fields and obj is None:
            form.base_fields["geom"].widget = forms.HiddenInput()
        return form

    def geolocalise(self, instance):
        return instance.geom is not None

    geolocalise.boolean = True
    geolocalise.short_description = "Géolocalisé"

    def renseignee(self, instance):
        return instance.accessibilite is not None

    renseignee.boolean = True
    renseignee.short_description = "Renseignée"

    def voie_ou_lieu_dit(self, instance):
        if instance.voie is not None:
            num = ""
            if instance.numero is not None:
                num = instance.numero
            return (num + " " + instance.voie).strip()
        elif instance.lieu_dit is not None:
            return instance.lieu_dit
        else:
            return "Inconnu"

    voie_ou_lieu_dit.short_description = "Voie ou lieu-dit"

    def view_link(self, obj):
        return mark_safe(
            f'<a target="_blank" href="{obj.get_absolute_url()}">Voir</a>'
        )

    view_link.short_description = ""

    def view_search(self, obj):
        terms = f"{obj.nom} {obj.voie} {obj.commune}"
        return mark_safe(
            f'<a target="_blank" href="https://www.google.fr/search?source=hp&q={terms}">Rech.</a>'
        )

    view_search.short_description = ""


# General admin heading & labels
warn = " (LOCAL)" if settings.DEBUG else ""
admin.site.site_title = f"Access4all admin{warn}"
admin.site.site_header = f"Access4all admin{warn}"
admin.site.index_title = f"Access4all administration{warn}"
