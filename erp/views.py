import json

from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.generic.base import TemplateView

from .communes import COMMUNES
from .forms import ViewAccessibiliteForm
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
        # FIXME: find a better trick to list erps having an accessibilite first
        queryset = queryset.order_by("accessibilite")
        # We can't hammer the pages with too many entries, hard-limiting here
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
            erp = get_object_or_404(Erp, published=True, id=self.kwargs["erp"])
            context["erp"] = erp
            if erp.has_accessibilite():
                form = ViewAccessibiliteForm(instance=erp.accessibilite)
                context["accessibilite_data"] = form.get_accessibilite_data()
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
