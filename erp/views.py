import json

from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic

from .communes import COMMUNES
from .models import Activite, Erp
from .serializers import ErpSerializer

# TODO
# - détails d'access


def home(request):
    return render(request, "erps/index.html", {"communes": COMMUNES})


class App(generic.ListView):
    model = Erp
    queryset = (
        Erp.objects.published()
        .having_an_activite()
        .prefetch_related("activite")
        .select_related("activite")
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
                queryset = queryset.filter(activite_id=self.kwargs["activite"])
            if "erp" in self.kwargs:
                queryset = queryset.filter(id=self.kwargs["erp"])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commune"] = self.commune
        context["commune_json"] = json.dumps(self.commune)
        context["search_terms"] = self.search_terms
        context["activites"] = Activite.objects.with_erp_counts(
            commune=self.commune["nom"], order_by="nom"
        )
        if "activite" in self.kwargs:
            context["current_activite"] = get_object_or_404(
                Activite, pk=self.kwargs["activite"]
            )
        if "erp" in self.kwargs:
            context["erp"] = get_object_or_404(Erp, id=self.kwargs["erp"])
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
