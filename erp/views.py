import json

from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.generic.base import TemplateView

from .communes import COMMUNES
from .forms import ViewAccessibiliteForm
from .models import Accessibilite, Activite, Cheminement, Erp
from .serializers import ErpSerializer


def handler404(request, exception):
    return render(
        request,
        "404.html",
        context={"communes": COMMUNES, "exception": exception},
        status=404,
    )


def handler500(request):
    return render(
        request, "500.html", context={"communes": COMMUNES}, status=500
    )


def home(request):
    latest = (
        Erp.objects.published()
        .geolocated()
        .select_related("activite")
        .having_an_accessibilite()
        .order_by("-created_at")[:15]
    )
    return render(
        request, "index.html", context={"communes": COMMUNES, "latest": latest}
    )


def find_commune_by_slug_or_404(commune_slug):
    for key, commune in COMMUNES.items():
        if commune_slug == commune["slug"]:
            return COMMUNES[key]
    raise Http404(f"Cette commune est introuvable ({commune}).")


@cache_page(60 * 15)
def autocomplete(request, commune):
    suggestions = []
    q = request.GET.get("q", "")
    commune_nom = find_commune_by_slug_or_404(commune)["nom"]
    if len(q) < 3:
        return JsonResponse({"suggestions": suggestions})
    qs = (
        Erp.objects.published()
        .geolocated()
        .in_commune(commune_nom)
        .search(q)[:7]
    )
    for erp in qs:
        score = (erp.rank + erp.similarity - (erp.distance / 6)) * 60
        score = 10 if score > 10 else score
        suggestions.append(
            {
                "value": erp.nom + ", " + erp.short_adresse,
                "data": {
                    "score": score,
                    "url": (
                        erp.get_absolute_url()
                        + "?around="
                        + str(erp.geom.coords[1])
                        + ","
                        + str(erp.geom.coords[0])
                    ),
                },
            }
        )
    suggestions = sorted(
        suggestions, key=lambda s: s["data"]["score"], reverse=True
    )
    return JsonResponse({"suggestions": suggestions})


class EditorialView(TemplateView):
    template_name = "editorial/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["communes"] = COMMUNES
        return context


class App(generic.ListView):
    model = Erp
    queryset = (
        Erp.objects.published().geolocated()
        # .having_an_activite()
        .select_related("activite", "accessibilite")
    )
    template_name = "erps/commune.html"

    @property
    def around(self):
        raw = self.request.GET.get("around")
        if raw is None:
            return
        try:
            rlon, rlat = raw.split(",")
            return (float(rlon), float(rlat))
        except (IndexError, ValueError, TypeError) as err:
            return

    @property
    def commune(self):
        return find_commune_by_slug_or_404(self.kwargs["commune"])

    @property
    def search_terms(self):
        q = self.request.GET.get("q", "").strip()
        if len(q) >= 2:
            return q

    def get_queryset(self):
        queryset = super(App, self).get_queryset()
        queryset = queryset.in_commune(self.commune["nom"])
        if self.search_terms is not None:
            queryset = queryset.search(self.search_terms)
        else:
            if "activite_slug" in self.kwargs:
                if self.kwargs["activite_slug"] == "non-categorises":
                    queryset = queryset.filter(activite__isnull=True)
                else:
                    queryset = queryset.filter(
                        activite__slug=self.kwargs["activite_slug"]
                    )
            # FIXME: find a better trick to list erps having an accessibilite first,
            # so we can keep name ordering
            queryset = queryset.order_by("accessibilite")
        if self.around is not None:
            queryset = queryset.nearest(self.around)
        # We can't hammer the pages with too many entries, hard-limiting here
        return queryset[:500]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["around"] = (
            list(self.around) if self.around is not None else self.around
        )
        context["commune"] = self.commune
        context["communes"] = COMMUNES
        context["commune_json"] = json.dumps(self.commune)
        context["search_terms"] = self.search_terms
        context["activites"] = Activite.objects.with_erp_counts(
            commune=self.commune["nom"], order_by="nom"
        )
        if (
            "activite_slug" in self.kwargs
            and self.kwargs["activite_slug"] != "non-categorises"
        ):
            context["current_activite"] = get_object_or_404(
                Activite, slug=self.kwargs["activite_slug"]
            )
        if "erp_slug" in self.kwargs:
            erp = get_object_or_404(
                Erp.objects.select_related("accessibilite"),
                published=True,
                slug=self.kwargs["erp_slug"],
            )
            context["erp"] = erp
            if erp.has_accessibilite():
                form = ViewAccessibiliteForm(instance=erp.accessibilite)
                context["accessibilite_data"] = form.get_accessibilite_data()
        serializer = ErpSerializer()
        context["geojson_list"] = serializer.serialize(
            context["object_list"],
            geometry_field="geom",
            use_natural_foreign_keys=True,
            fields=[
                "pk",
                "nom",
                "activite__nom",
                "adresse",
                "absolute_url",
                "has_accessibilite",
            ],
        )
        return context


def to_betagouv(self):
    return redirect("https://beta.gouv.fr/startups/access4all.html")
