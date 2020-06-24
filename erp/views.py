from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import F
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.generic.base import TemplateView

from .forms import (
    AdminAccessibiliteForm,
    PublicClaimForm,
    PublicErpAdminInfosForm,
    PublicErpEditInfosForm,
    PublicEtablissementSearchForm,
    PublicLocalisationForm,
    PublicPublicationForm,
    PublicSiretSearchForm,
    ViewAccessibiliteForm,
)
from .models import Accessibilite, Activite, Commune, Erp
from .serializers import SpecialErpSerializer
from . import schema
from . import sirene


def handler403(request, exception):
    return render(request, "403.html", context={"exception": exception}, status=403,)


def handler404(request, exception):
    return render(request, "404.html", context={"exception": exception}, status=404,)


def handler500(request):
    return render(request, "500.html", context={}, status=500)


def home(request):
    communes_qs = Commune.objects.erp_stats()[:12]
    latest = (
        Erp.objects.published()
        .geolocated()
        .select_related("activite", "commune_ext")
        .having_an_accessibilite()
        .order_by("-created_at")[:17]
    )
    search_results = None
    search = request.GET.get("q")
    localize = request.GET.get("localize")
    pager = None
    pager_base_url = None
    page_number = 1
    lat = None
    lon = None
    if search and len(search) > 0:
        erp_qs = (
            Erp.objects.published()
            .geolocated()
            .select_related("accessibilite", "activite", "commune_ext")
            .search(search)
        )
        if request.GET.get("access") == "1":
            erp_qs = erp_qs.having_an_accessibilite()
        if localize == "1":
            try:
                (lat, lon) = (
                    float(request.GET.get("lat")),
                    float(request.GET.get("lon")),
                )
                erp_qs = erp_qs.nearest((lat, lon,)).order_by("distance")
            except ValueError:
                pass
        paginator = Paginator(erp_qs, 10)
        page_number = request.GET.get("page", 1)
        pager = paginator.get_page(page_number)
        pager_base_url = f"?q={search or ''}&localize={localize or ''}&lat={lat or ''}&lon={lon or ''}"
        search_results = {
            "communes": Commune.objects.search(search).order_by(
                F("population").desc(nulls_last=True)
            )[:4],
            "pager": pager,
        }
    return render(
        request,
        "index.html",
        context={
            "empty_query": "q" in request.GET and not search,
            "pager": pager,
            "pager_base_url": pager_base_url,
            "page_number": page_number,
            "localize": localize,
            "lat": request.GET.get("lat"),
            "lon": request.GET.get("lon"),
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
        return context


class BaseListView(generic.ListView):
    model = Erp
    queryset = (
        Erp.objects.published()
        .select_related("activite", "accessibilite", "commune_ext")
        .geolocated()
    )
    _commune = None

    @property
    def around(self):
        raw = self.request.GET.get("around")
        if raw is None:
            return
        try:
            rlon, rlat = raw.split(",")
            return (float(rlon), float(rlat))
        except (IndexError, ValueError, TypeError):
            return None

    @property
    def commune(self):
        if self._commune is None:
            self._commune = get_object_or_404(
                Commune.objects.select_related(), slug=self.kwargs["commune"]
            )
        return self._commune

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
                Erp.objects.select_related("accessibilite").published(),
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


def mon_compte(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    return render(request, "compte/index.html",)


def mes_erps(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    qs = Erp.objects.select_related("accessibilite", "activite", "commune_ext").filter(
        user_id=request.user.pk
    )
    erp_total_count = qs.count()
    erp_published_count = qs.filter(published=True).count()
    erp_non_published_count = qs.filter(published=False).count()
    erp_filled_count = qs.filter(accessibilite__isnull=False).count()
    erp_non_filled_count = qs.filter(accessibilite__isnull=True).count()
    published = request.GET.get("published")
    if published == "1":
        qs = qs.filter(published=True)
    elif published == "0":
        qs = qs.filter(published=False)
    filled = request.GET.get("filled")
    if filled == "1":
        qs = qs.filter(accessibilite__isnull=False)
    elif filled == "0":
        qs = qs.filter(accessibilite__isnull=True)
    qs = qs.filter(user_id=request.user.pk).order_by("-updated_at")
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page", 1)
    pager = paginator.get_page(page_number)
    return render(
        request,
        "compte/mes_erps.html",
        context={
            "erp_total_count": erp_total_count,
            "erp_published_count": erp_published_count,
            "erp_non_published_count": erp_non_published_count,
            "erp_filled_count": erp_filled_count,
            "erp_non_filled_count": erp_non_filled_count,
            "pager": pager,
            "pager_base_url": f"?published={published or ''}&filled={filled or ''}",
            "filter_published": published,
            "filter_filled": filled,
        },
    )


def to_betagouv(self):
    return redirect("https://beta.gouv.fr/startups/access4all.html")


def find_sirene_etablissements(name_form):
    results = sirene.find_etablissements(
        name_form.cleaned_data.get("nom"), name_form.cleaned_data.get("lieu"), limit=15,
    )
    for result in results:
        result["exists"] = Erp.objects.exists_by_siret(result["siret"])
    return results


@login_required
def contrib_start(request):
    siret_search_error = name_search_error = name_search_results = None
    (siret_form, name_form) = (PublicSiretSearchForm(), PublicEtablissementSearchForm())
    if request.method == "POST":
        if request.POST.get("type") == "by-name":
            name_form = PublicEtablissementSearchForm(request.POST)
            if name_form.is_valid():
                try:
                    name_search_results = find_sirene_etablissements(name_form)
                except RuntimeError as err:
                    name_search_error = str(err)
        elif request.POST.get("type") == "by-siret":
            siret_form = PublicSiretSearchForm(request.POST)
            if siret_form.is_valid():
                try:
                    siret_info = sirene.get_siret_info(siret_form.cleaned_data["siret"])
                    data = sirene.base64_encode_etablissement(siret_info)
                    return redirect(reverse("contrib_admin_infos") + "?data=" + data)
                except RuntimeError as err:
                    siret_search_error = err
    return render(
        request,
        template_name="contrib/0-start.html",
        context={
            "step": 1,
            "name_form": name_form,
            "name_search_results": name_search_results,
            "siret_form": siret_form,
            "name_search_error": name_search_error,
            "siret_search_error": siret_search_error,
        },
    )


@login_required
def contrib_admin_infos(request):
    data = None
    data_error = None
    if request.method == "POST":
        form = PublicErpAdminInfosForm(request.POST)
        if form.is_valid():
            erp = form.save(commit=False)
            erp.published = False
            erp.user = request.user
            erp.save()
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        encoded_data = request.GET.get("data")
        if encoded_data is not None:
            try:
                data = sirene.base64_decode_etablissement(encoded_data)
            except RuntimeError as err:
                data_error = err
        form = PublicErpAdminInfosForm(data)
    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "form": form,
            "has_data": data is not None,
            "data_error": data_error,
        },
    )


@login_required
def contrib_edit_infos(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    if request.method == "POST":
        form = PublicErpEditInfosForm(request.POST, instance=erp)
        if form.is_valid():
            erp = form.save()
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        form = PublicErpAdminInfosForm(instance=erp)
    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={"step": 1, "erp": erp, "form": form, "has_data": False,},
    )


@login_required
def contrib_localisation(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    if request.method == "POST":
        form = PublicLocalisationForm(request.POST)
        if form.is_valid():
            lat = form.cleaned_data.get("lat")
            lon = form.cleaned_data.get("lon")
            erp.geom = Point(x=lon, y=lat, srid=4326)
            erp.save()
            return redirect("contrib_transport", erp_slug=erp.slug)
    elif erp.geom is not None:
        form = PublicLocalisationForm(
            {"lon": erp.geom.coords[0], "lat": erp.geom.coords[1]}
        )
    return render(
        request,
        template_name="contrib/2-localisation.html",
        context={"step": 1, "erp": erp, "form": form,},
    )


def process_accessibilite_form(
    request, erp_slug, step, form_fields, template_name, redirect_route
):
    "Traitement générique des requêtes sur les formulaires d'accessibilité"

    erp = get_object_or_404(
        Erp.objects.select_related("accessibilite"), slug=erp_slug, user=request.user,
    )
    accessibilite = erp.accessibilite if hasattr(erp, "accessibilite") else None
    if request.method == "POST":
        Form = modelform_factory(
            Accessibilite, form=AdminAccessibiliteForm, fields=form_fields
        )
        form = Form(request.POST, instance=accessibilite)
        if form.is_valid():
            accessibilite = form.save(commit=False)
            accessibilite.erp = erp
            accessibilite.save()
            form.save_m2m()
            return redirect(redirect_route, erp_slug=erp.slug)
    else:
        form = AdminAccessibiliteForm(instance=accessibilite)

    return render(
        request,
        template_name=template_name,
        context={
            "step": step,
            "erp": erp,
            "form": form,
            "accessibilite": accessibilite,
        },
    )


@login_required
def contrib_transport(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        2,
        schema.get_section_fields(schema.SECTION_TRANSPORT),
        "contrib/3-transport.html",
        "contrib_stationnement",
    )


@login_required
def contrib_stationnement(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        2,
        schema.get_section_fields(schema.SECTION_STATIONNEMENT),
        "contrib/4-stationnement.html",
        "contrib_exterieur",
    )


@login_required
def contrib_exterieur(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        3,
        schema.get_section_fields(schema.SECTION_CHEMINEMENT_EXT),
        "contrib/5-exterieur.html",
        "contrib_entree",
    )


@login_required
def contrib_entree(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        4,
        schema.get_section_fields(schema.SECTION_ENTREE),
        "contrib/6-entree.html",
        "contrib_accueil",
    )


@login_required
def contrib_accueil(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        5,
        schema.get_section_fields(schema.SECTION_ACCUEIL),
        "contrib/7-accueil.html",
        "contrib_sanitaires",
    )


@login_required
def contrib_sanitaires(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        6,
        schema.get_section_fields(schema.SECTION_SANITAIRES),
        "contrib/8-sanitaires.html",
        "contrib_autre",
    )


@login_required
def contrib_autre(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        7,
        schema.get_section_fields(schema.SECTION_LABELS),
        "contrib/9-autre.html",
        "contrib_publication",
    )


@login_required
def contrib_publication(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    initial = (
        {"commentaire": erp.accessibilite.commentaire} if erp.accessibilite else {}
    )
    if request.method == "POST":
        form = PublicPublicationForm(request.POST, instance=erp, initial=initial)
        if form.is_valid():
            erp = form.save(commit=False)
            erp.published = True
            erp.save()
            erp.accessibilite.commentaire = form.data.get("commentaire")
            erp.accessibilite.save()
            return redirect("mes_erps")
    else:
        form = PublicPublicationForm(instance=erp, initial=initial)
    return render(
        request,
        template_name="contrib/10-publication.html",
        context={"step": 8, "erp": erp, "form": form,},
    )


@login_required
def contrib_claim(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user__isnull=True, published=True)
    if request.method == "POST":
        form = PublicClaimForm(request.POST)
        if form.is_valid():
            erp.user = request.user
            erp.save()
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        form = PublicClaimForm()
    return render(
        request, template_name="contrib/claim.html", context={"erp": erp, "form": form}
    )
