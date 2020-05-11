from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.generic.base import TemplateView

from .communes import COMMUNES
from .forms import ViewAccessibiliteForm
from .models import Accessibilite, Activite, Commune, Erp
from .serializers import SpecialErpSerializer


def handler404(request, exception):
    return render(
        request,
        "404.html",
        context={"communes": COMMUNES, "exception": exception},
        status=404,
    )


def handler500(request):
    return render(request, "500.html", context={"communes": COMMUNES}, status=500)


def home(request):
    communes_qs = Commune.objects.annotate(
        erp_count=Count(
            "erp", filter=Q(erp__accessibilite__isnull=False), distinct=True
        )
    )
    communes_qs = communes_qs.order_by("-erp_count")[:12]
    latest = (
        Erp.objects.published()
        .geolocated()
        .select_related("activite", "commune_ext")
        .having_an_accessibilite()
        .order_by("-created_at")[:7]
    )
    search_results = None
    search = request.GET.get("q")
    if search and len(search) > 1:
        terms = search.strip().split(" ")
        clauses = Q()
        for term in terms:
            if term.isdigit() and len(term) == 5:
                clauses = clauses | Q(code_postaux__contains=[term])
            if len(term) > 2:
                clauses = clauses | Q(nom__unaccent__icontains=term)
        search_results = {
            "communes": Commune.objects.filter(clauses).order_by("-superficie")[:4],
            "erps": (
                Erp.objects.published()
                .geolocated()
                .select_related("activite", "commune_ext")
                .search(search)[:10]
            ),
        }
    return render(
        request,
        "index.html",
        context={
            "search": search,
            "communes": communes_qs,
            "latest": latest,
            "search_results": search_results,
        },
    )


@cache_page(60 * 15)
def autocomplete(request):
    suggestions = []
    q = request.GET.get("q", "")
    commune_slug = request.GET.get("commune_slug")
    if len(q) < 3:
        return JsonResponse({"suggestions": suggestions})
    qs = Erp.objects.published().geolocated()
    if commune_slug:
        qs = qs.filter(commune_ext__slug=commune_slug)
    qs = qs.search(q)[:7]
    for erp in qs:
        score = (erp.rank + erp.similarity - (erp.distance_nom / 6)) * 60
        score = 10 if score > 10 else score
        suggestions.append(
            {
                "value": erp.nom + ", " + erp.adresse,
                "data": {
                    "score": score,
                    "activite": erp.activite and erp.activite.slug,
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
    suggestions = sorted(suggestions, key=lambda s: s["data"]["score"], reverse=True)
    return JsonResponse({"suggestions": suggestions})


class EditorialView(TemplateView):
    template_name = "editorial/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["communes"] = COMMUNES
        return context


class BaseListView(generic.ListView):
    model = Erp
    queryset = (
        Erp.objects.published()
        .select_related("activite", "accessibilite", "commune_ext")
        .geolocated()
    )

    @property
    def around(self):
        raw = self.request.GET.get("around")
        if raw is None:
            return
        try:
            rlon, rlat = raw.split(",")
            return (float(rlon), float(rlat))
        except (IndexError, ValueError, TypeError) as err:
            return None

    @property
    def commune(self):
        return get_object_or_404(Commune, slug=self.kwargs["commune"])

    @property
    def search_terms(self):
        q = self.request.GET.get("q", "").strip()
        if len(q) >= 2:
            return q

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.in_commune(self.commune)
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


class App(BaseListView):
    "Static, template-based Web application views."
    template_name = "erps/commune.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["around"] = (
            list(self.around) if self.around is not None else self.around
        )
        context["commune"] = self.commune
        context["communes"] = COMMUNES
        context["commune_json"] = self.commune.toTemplateJson()
        context["search_terms"] = self.search_terms
        context["activites"] = Activite.objects.in_commune(
            self.commune
        ).with_erp_counts()
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
        serializer = SpecialErpSerializer()
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
