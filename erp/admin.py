import nested_admin

from django import forms
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django.conf import settings
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe

# from import_export.admin import ImportExportModelAdmin

from .departements import DEPARTEMENTS
from .forms import (
    AdminActiviteForm,
    AdminAccessibiliteForm,
    AdminCommuneForm,
    AdminErpForm,
)

# from .imports import ErpResource
from .models import (
    Activite,
    Commune,
    Erp,
    Label,
    Accessibilite,
)
from . import schema


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    form = AdminActiviteForm
    list_display = ("nom", "erp_count", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(erp_count=Count("erp", distinct=True),)
        return queryset

    def erp_count(self, obj):
        return obj.erp_count


class HavingErpsFilter(admin.SimpleListFilter):
    title = "renseignement d'ERP"
    parameter_name = "having_erp"

    def lookups(self, request, model_admin):
        return [(1, "Avec ERP"), (0, "Sans ERP")]

    def queryset(self, request, queryset):
        communes = queryset.annotate(erp_count=Count("erp", distinct=True))
        if self.value() == "1":
            return communes.filter(erp_count__gt=0)
        elif self.value() == "0":
            return communes.filter(erp_count=0)
        else:
            return queryset


class DepartementFilter(admin.SimpleListFilter):
    title = "Département"
    parameter_name = "departement"
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"

    def lookups(self, request, model_admin):
        values = Commune.objects.distinct("departement").order_by("departement")
        return (
            (v.departement, f"{v.departement} - {DEPARTEMENTS[v.departement]['nom']}")
            for v in values
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(departement=self.value())


@admin.register(Commune)
class CommuneAdmin(OSMGeoAdmin, admin.ModelAdmin):
    form = AdminCommuneForm
    point_zoom = 13
    map_height = 300
    list_display = ("departement", "nom", "erp_count", "code_insee", "code_postaux")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom", "code_insee", "code_postaux")
    list_filter = [
        HavingErpsFilter,
        DepartementFilter,
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(erp_count=Count("erp", distinct=True),)
        return queryset

    def erp_count(self, obj):
        return obj.erp_count

    erp_count.short_description = "ERPs"


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("nom", "created_at", "updated_at")
    list_display_links = ("nom",)
    ordering = ("nom",)
    search_fields = ("nom",)


class AccessibiliteInline(nested_admin.NestedStackedInline):
    model = Accessibilite
    form = AdminAccessibiliteForm
    autocomplete_fields = ["labels"]
    fieldsets = schema.get_admin_fieldsets()

    def get_formset(self, request, obj=None, **kwargs):
        # see https://stackoverflow.com/a/37558444/330911
        formset = super(AccessibiliteInline, self).get_formset(request, obj, **kwargs)
        form = formset.form
        if "labels" in form.base_fields:
            form.base_fields["labels"].widget.can_add_related = False
            form.base_fields["labels"].widget.can_change_related = False
            form.base_fields["labels"].widget.can_delete_related = False
        return formset


class CommuneFilter(admin.SimpleListFilter):
    # see https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
    title = "Commune"
    parameter_name = "commune"
    template = "django_admin_listfilter_dropdown/dropdown_filter.html"

    def lookups(self, request, model_admin):
        values = (
            Erp.objects.prefetch_related("commune_ext")
            .filter(commune_ext__isnull=False)
            .distinct("commune_ext__nom")
            .order_by("commune_ext__nom")
        )
        return (
            (v.commune_ext.id, f"{v.commune_ext.nom} ({v.commune_ext.departement})")
            for v in values
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(commune_ext__pk=self.value())


@admin.register(Erp)
class ErpAdmin(OSMGeoAdmin, nested_admin.NestedModelAdmin):
    class Media:
        css = {"all": ("admin/a4a-addons.css",)}
        js = (
            "js/jquery.autocomplete.min.js",
            "js/forms.js",
            "admin/js/a4a-admin.js",
            "admin/js/a4a-autocomplete.js",
        )

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
        "source",
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
    readonly_fields = ["user"]
    point_zoom = 18
    map_height = 300
    save_on_top = True
    search_fields = ["nom", "activite__nom", "code_postal", "commune"]
    autocomplete_fields = ["activite", "commune_ext"]
    scrollable = False
    sortable_by = ("nom", "activite__nom", "code_postal", "commune")
    view_on_site = True

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "photon_autocomplete",
                    "activite",
                    "nom",
                    "siret",
                    "user",
                    "published",
                ]
            },
        ),
        (
            "Localisation",
            {
                "fields": [
                    "ban_autocomplete",
                    "numero",
                    "voie",
                    "lieu_dit",
                    "code_postal",
                    "commune",
                    # "commune_ext", # note: this field is handled on model clean()
                    "code_insee",
                    "geom",
                ]
            },
        ),
        ("Contact", {"fields": ["telephone", "site_internet", "contact_email"],},),
    ]

    def assign_activite(self, request, queryset):
        if "apply" in request.POST:
            try:
                queryset.update(activite_id=int(request.POST["activite"]))
                self.message_user(request, f"{queryset.count()} ERP ont été modifiés.")
            except (KeyError, TypeError):
                pass
            return HttpResponseRedirect(request.get_full_path())

        return render(
            request,
            "admin/assign_activite.html",
            context={"erps": queryset, "activites": Activite.objects.all()},
        )

    assign_activite.short_description = "Assigner une nouvelle catégorie"

    def geolocalise(self, instance):
        return instance.geom is not None

    geolocalise.boolean = True
    geolocalise.short_description = "Géo"

    def get_form(self, request, obj=None, **kwargs):
        # see https://code.djangoproject.com/ticket/9071#comment:24
        form = super().get_form(request, obj, **kwargs)
        if "activite" in form.base_fields:
            form.base_fields["activite"].widget.can_add_related = False
            form.base_fields["activite"].widget.can_change_related = False
            form.base_fields["activite"].widget.can_delete_related = False
        # hide geom field on new obj
        if "geom" in form.base_fields and obj is None:
            form.base_fields["geom"].widget = forms.HiddenInput()
        return form

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if not request.user.is_superuser:
            return (f for f in list_display if f != "source")
        return list_display

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related("commune_ext")
        return queryset

    def has_change_permission(self, request, obj=None):
        # see https://www.b-list.org/weblog/2008/dec/24/admin/
        # initial perm checks (including group ones, eg observateurs)
        allow = super().has_change_permission(request, obj)
        if not allow:
            return False
        # every staff user with create perm can create new erps
        if obj is None:
            return True
        return obj.editable_by(request.user)

    def publish(self, request, queryset):
        queryset.update(published=True)

    publish.short_description = "Publier"

    def renseignee(self, instance):
        return instance.accessibilite is not None

    renseignee.boolean = True
    renseignee.short_description = "Renseignée"

    def save_model(self, request, obj, form, change):
        if not change or obj.user is None:
            obj.user = request.user

        super().save_model(request, obj, form, change)

    def unpublish(self, request, queryset):
        queryset.update(published=False)

    unpublish.short_description = "Mettre hors ligne"

    def view_link(self, obj):
        return mark_safe(f'<a target="_blank" href="{obj.get_absolute_url()}">Voir</a>')

    view_link.short_description = ""

    def view_search(self, obj):
        terms = f"{obj.nom} {obj.voie} {obj.commune}"
        return mark_safe(
            f'<a target="_blank" href="https://www.google.fr/search?source=hp&q={terms}">Rech.</a>'
        )

    view_search.short_description = ""

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


# General admin heading & labels
warn = " (LOCAL)" if settings.DEBUG else ""
admin.site.site_title = f"Access4all admin{warn}"
admin.site.site_header = f"Access4all admin{warn}"
admin.site.index_title = f"Access4all administration{warn}"
