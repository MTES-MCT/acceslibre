import json

from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.shortcuts import redirect, render
from django.views import generic

from .models import Activite, Erp
from .serializers import ErpSerializer

# TODO
# - slugs
# - design
# - page ERP
# - détails d'access

COMMUNES = {
    "courbevoie": {
        "nom": "Courbevoie",
        "center": (48.8976, 2.2574),
        "zoom": 15,
    },
    "lorient": {"nom": "Lorient", "center": (47.7494, -3.3792), "zoom": 14},
    "lyon": {"nom": "Lyon", "center": (45.7578, 4.8351), "zoom": 13},
    "rueil-malmaison": {
        "nom": "Rueil-Malmaison",
        "center": (48.8718, 2.1806),
        "zoom": 14,
    },
    "villeurbanne": {
        "nom": "Villeurbanne",
        "center": (45.7720, 4.8898),
        "zoom": 14,
    },
}


def home(request):
    return render(request, "erps/index.html", {"communes": COMMUNES})


class Commune(generic.ListView):
    model = Erp
    queryset = Erp.objects.filter(
        published=True, activite__isnull=False
    ).select_related("activite")
    template_name = "erps/commune.html"

    @property
    def commune(self):
        return self.kwargs["commune"]

    def get_queryset(self):
        if self.commune not in COMMUNES:
            raise RuntimeError("Commune invalide.")  # XXX: Not found error
        queryset = super(Commune, self).get_queryset()
        queryset = queryset.filter(commune__iexact=self.commune)
        if "activite" in self.kwargs:
            queryset = queryset.filter(activite__nom=self.kwargs["activite"])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["commune_name"] = COMMUNES[self.commune]["nom"]
        context["commune_slug"] = self.commune
        context["commune_info"] = json.dumps(COMMUNES[self.commune])
        context["activites"] = Activite.objects.with_erp_counts(
            commune=self.commune, order_by="nom"
        )
        # see https://stackoverflow.com/a/56557206/330911
        serializer = ErpSerializer()
        context["geojson_list"] = serializer.serialize(
            self.get_queryset(),
            geometry_field="geom",
            use_natural_foreign_keys=True,
            fields=["nom", "activite__nom", "adresse"],
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
