import json

from django import forms
from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.generic.base import TemplateView

from .communes import COMMUNES
from .models import Accessibilite, Activite, Cheminement, Erp
from .serializers import ErpSerializer


def home(request):
    latest = (
        Erp.objects.published()
        .select_related("activite")
        .having_an_accessibilite()
        .order_by("-created_at")[:15]
    )
    return render(
        request, "index.html", {"communes": COMMUNES, "latest": latest}
    )


class EditorialView(TemplateView):
    template_name = "editorial/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["communes"] = COMMUNES
        return context


class CheminementForm(forms.ModelForm):
    class Meta:
        model = Cheminement
        exclude = ("pk", "accessibilite", "type", "nom")


class AccessibiliteForm(forms.ModelForm):
    class Meta:
        model = Accessibilite
        exclude = ("pk", "erp", "labels")

    fieldsets = {
        "Entrée": {
            "icon": "entrance",
            "tabid": "entree",
            "fields": [
                "entree_plain_pied",
                "entree_reperage",
                "entree_pmr",
                "entree_pmr_informations",
                "entree_interphone",
                "reperage_vitres",
                "guidage_sonore",
                "largeur_mini",
                "rampe",
                "aide_humaine",
                "escalier_marches",
                "escalier_reperage",
                "escalier_main_courante",
                "ascenseur",
            ],
        },
        "Stationnement": {
            "icon": "car",
            "tabid": "stationnement",
            "fields": [
                "stationnement_presence",
                "stationnement_pmr",
                "stationnement_ext_presence",
                "stationnement_ext_pmr",
            ],
        },
        "Accueil": {
            "icon": "users",
            "tabid": "accueil",
            "fields": [
                "accueil_visibilite",
                "accueil_personnels",
                "accueil_equipements_malentendants",
                "accueil_prestations",
            ],
        },
        "Sanitaires": {
            "icon": "male-female",
            "tabid": "sanitaires",
            "fields": ["sanitaires_presence", "sanitaires_adaptes",],
        },
    }

    def get_accessibilite_data(self):
        data = {}
        for section, info in self.fieldsets.items():
            data[section] = {
                "icon": info["icon"],
                "tabid": info["tabid"],
                "fields": [],
            }
            for field_name in info["fields"]:
                field = self[field_name]
                # TODO: deconstruct field to make it serializable -> future API
                data[section]["fields"].append(field)
        cheminements = self.instance.cheminement_set.all()
        if len(cheminements) > 0:
            data["Cheminements"] = {
                "icon": "path",
                "tabid": "cheminements",
                "sections": {},
            }
            for cheminement in cheminements:
                section = (
                    cheminement.get_type_display() + " : " + cheminement.nom
                )
                form = CheminementForm(instance=cheminement)
                data["Cheminements"]["sections"][section] = {
                    "icon": "path",
                    "tabid": cheminement.type,
                    "fields": [],
                }
                for field_name in form.fields:
                    # TODO: deconstruct field to make it serializable -> future API
                    field = form[field_name]
                    data["Cheminements"]["sections"][section]["fields"].append(
                        field
                    )
        return data


class App(generic.ListView):
    model = Erp
    queryset = (
        Erp.objects.published()
        # .having_an_activite()
        .select_related("activite", "accessibilite")
    )
    template_name = "erps/commune.html"

    @property
    def commune(self):
        for key, commune in COMMUNES.items():
            if self.kwargs["commune"] == commune["slug"]:
                return COMMUNES[key]
        raise Http404("Cette commune est introuvable.")

    @property
    def search_terms(self):
        q = self.request.GET.get("q", "").strip()
        if len(q) >= 2:
            return q

    def get_queryset(self):
        queryset = super(App, self).get_queryset()
        queryset = queryset.filter(commune__iexact=self.commune["nom"])
        if self.search_terms is not None:
            queryset = queryset.search(self.search_terms)
        else:
            if "activite" in self.kwargs:
                if self.kwargs["activite"] is 0:
                    queryset = queryset.filter(activite__isnull=True)
                else:
                    queryset = queryset.filter(
                        activite_id=self.kwargs["activite"]
                    )
            if "erp" in self.kwargs:
                queryset = queryset.filter(id=self.kwargs["erp"])
        return queryset[:500]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commune"] = self.commune
        context["communes"] = COMMUNES
        context["commune_json"] = json.dumps(self.commune)
        context["search_terms"] = self.search_terms
        context["activites"] = Activite.objects.with_erp_counts(
            commune=self.commune["nom"], order_by="nom"
        )
        if "activite" in self.kwargs and self.kwargs["activite"] is not 0:
            context["current_activite"] = get_object_or_404(
                Activite, pk=self.kwargs["activite"]
            )
        if "erp" in self.kwargs:
            erp = get_object_or_404(Erp, id=self.kwargs["erp"])
            context["erp"] = erp
            if hasattr(erp, "accessibilite") and erp.accessibilite is not None:
                form = AccessibiliteForm(instance=erp.accessibilite)
                context["accessibilite_data"] = form.get_accessibilite_data()
        # if len(context["object_list"]) == 1:
        #     context["erp"] = context["object_list"][0]
        # see https://stackoverflow.com/a/56557206/330911
        serializer = ErpSerializer()
        context["geojson_list"] = serializer.serialize(
            context["object_list"],
            geometry_field="geom",
            use_natural_foreign_keys=True,
            fields=["pk", "nom", "activite__nom", "adresse", "absolute_url",],
        )
        return context


class Geoloc(generic.ListView):
    model = Erp
    queryset = Erp.objects.nearest(2.352222, 48.856613)[0:10]  # paris center
    template_name = "erps/commune.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["geojson_list"] = serialize(
            "geojson", self.queryset, geometry_field="geom", fields=("nom",)
        )
        return context


def to_betagouv(self):
    return redirect("https://beta.gouv.fr/startups/access4all.html")
