import reversion

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.core.paginator import Paginator
from django.db.models import F
from django.forms import modelform_factory
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from django_registration.backends.activation.views import (
    ActivationView,
    RegistrationView,
)

from core import mailer

from .forms import (
    AdminAccessibiliteForm,
    PublicClaimForm,
    PublicErpDeleteForm,
    PublicErpAdminInfosForm,
    PublicErpEditInfosForm,
    PublicEtablissementSearchForm,
    PublicLocalisationForm,
    PublicPublicationForm,
    PublicPublicErpSearchForm,
    PublicSiretSearchForm,
    ViewAccessibiliteForm,
)
from .models import Accessibilite, Activite, Commune, Erp, Vote
from .provider import sirene
from . import naf
from . import public_erp
from . import schema
from . import serializers
from . import versioning


def handler403(request, exception):
    return render(request, "403.html", context={"exception": exception}, status=403,)


def handler404(request, exception):
    return render(request, "404.html", context={"exception": exception}, status=404,)


def handler500(request):
    return render(request, "500.html", context={}, status=500)


def home(request):
    communes_qs = Commune.objects.erp_stats()[:12]
    latest = (
        Erp.objects.select_related("activite", "commune_ext")
        .published()
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
    if "q" in request.GET:
        erp_qs = Erp.objects.select_related(
            "accessibilite", "activite", "commune_ext"
        ).published()
        if len(search) > 0:
            erp_qs = erp_qs.search(search)
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


class CustomActivationCompleteView(TemplateView):
    def get_context_data(self, **kwargs):
        "Spread the next redirect value from qs param to template context key."
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomRegistrationView(RegistrationView):
    def get_email_context(self, activation_key):
        "Add the next redirect value to the email template context."
        context = super().get_email_context(activation_key)
        context["next"] = self.request.GET.get("next", "")
        return context


class CustomActivationView(ActivationView):
    def get_success_url(self, user=None):
        "Add the next redirect path to the success redirect url"
        url = super().get_success_url(user)
        next = self.request.GET.get("next", "")
        if not next and self.extra_context and "next" in self.extra_context:
            next = self.extra_context.get("next", "")
        return f"{url}?next={next}"


@cache_page(60 * 15)
def autocomplete(request):
    suggestions = []
    q = request.GET.get("q", "")
    commune_slug = request.GET.get("commune_slug")
    if len(q) < 3:
        return JsonResponse({"suggestions": suggestions})
    qs = Erp.objects.published()
    if commune_slug:
        qs = qs.filter(commune_ext__slug=commune_slug)
    qs = qs.search(q)[:7]
    for erp in qs:
        suggestions.append(
            {
                "value": erp.nom + ", " + erp.adresse,
                "data": {
                    "score": erp.rank,
                    "activite": erp.activite and erp.activite.slug,
                    "url": erp.get_absolute_url(),
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
    queryset = Erp.objects.select_related(
        "activite", "accessibilite", "commune_ext", "statuscheck"
    ).published()
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
            queryset = queryset.order_by("nom")
        if self.around is not None:
            queryset = queryset.nearest(self.around)
        # We can't hammer the pages with too many entries, hard-limiting here
        return queryset[:500]


class App(BaseListView):
    "Static, template-based Web application views."
    template_name = "erps/commune.html"

    def get(self, request, *args, **kwargs):
        if self.search_terms is not None and self.request.GET.get("scope") == "country":
            return redirect(reverse("home") + "?q=" + self.search_terms)
        return super().get(request, *args, **kwargs)

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
        context["activite_slug"] = self.kwargs.get("activite_slug")
        if (
            "activite_slug" in self.kwargs
            and self.kwargs["activite_slug"] != "non-categorises"
        ):
            context["current_activite"] = get_object_or_404(
                Activite, slug=self.kwargs["activite_slug"]
            )
        if "erp_slug" in self.kwargs:
            erp = get_object_or_404(
                Erp.objects.select_related(
                    "accessibilite", "activite", "commune_ext", "user", "statuscheck"
                )
                .published()
                .with_votes(),
                slug=self.kwargs["erp_slug"],
            )
            context["erp"] = erp
            if erp.has_accessibilite():
                form = ViewAccessibiliteForm(instance=erp.accessibilite)
                context["accessibilite_data"] = form.get_accessibilite_data()
            if self.request.user.is_authenticated:
                context["user_vote"] = Vote.objects.filter(
                    user=self.request.user, erp=erp
                ).first()
            context["object_list"] = (
                Erp.objects.select_related("accessibilite", "commune_ext", "activite")
                .published()
                .nearest([erp.geom.coords[1], erp.geom.coords[0]])
                .filter(distance__lt=Distance(km=20))[:16]
            )
        serializer = serializers.SpecialErpSerializer()
        context["geojson_list"] = serializer.serialize(
            context["object_list"],
            geometry_field="geom",
            use_natural_foreign_keys=True,
            fields=[
                "pk",
                "nom",
                "activite__nom",
                "activite__icon",
                "adresse",
                "absolute_url",
                "has_accessibilite",
            ],
        )
        return context


@login_required
def vote(request, erp_slug):
    if not request.user.is_active:
        raise Http404("Only active users can vote")
    erp = get_object_or_404(
        Erp, slug=erp_slug, published=True, accessibilite__isnull=False
    )
    if request.method == "POST":
        action = request.POST.get("action")
        comment = request.POST.get("comment") if action == "DOWN" else None
        vote = erp.vote(request.user, action, comment=comment)
        if vote:
            mailer.mail_admins(
                f"Vote {'positif' if vote.value == 1 else 'négatif'} pour {erp.nom} ({erp.commune_ext.nom})",
                "mail/vote_notification.txt",
                {
                    "erp": erp,
                    "vote": vote,
                    "SITE_NAME": settings.SITE_NAME,
                    "SITE_ROOT_URL": settings.SITE_ROOT_URL,
                },
            )
    return redirect(erp.get_absolute_url())


@login_required
def mon_compte(request):
    return render(request, "compte/index.html",)


@login_required
def mes_erps(request):
    qs = Erp.objects.select_related("accessibilite", "activite", "commune_ext").filter(
        user_id=request.user.pk
    )
    published_qs = qs.published()
    non_published_qs = qs.not_published()
    erp_total_count = qs.count()
    erp_published_count = published_qs.count()
    erp_non_published_count = non_published_qs.count()
    published = request.GET.get("published")
    if published == "1":
        qs = published_qs
    elif published == "0":
        qs = non_published_qs
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
            "pager": pager,
            "pager_base_url": f"?published={published or ''}",
            "filter_published": published,
        },
    )


def _mes_contributions_view(request, qs, recues=False):
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page", 1)
    pager = paginator.get_page(page_number)
    return render(
        request,
        "compte/mes_contributions.html",
        context={"pager": pager, "recues": recues},
    )


@login_required
def mes_contributions(request):
    qs = versioning.get_user_contributions(request.user)
    return _mes_contributions_view(request, qs)


@login_required
def mes_contributions_recues(request):
    qs = versioning.get_user_contributions_recues(request.user)
    return _mes_contributions_view(request, qs, recues=True)


def find_sirene_businesses(name_form):
    results = sirene.find_etablissements(
        name_form.cleaned_data.get("nom"),
        name_form.cleaned_data.get("lieu"),
        naf=name_form.cleaned_data.get("naf"),
        limit=15,
    )
    for result in results:
        result["exists"] = Erp.objects.find_by_siret(result["siret"])
    return results


def find_public_erps(public_erp_form):
    results = public_erp.get_code_insee_type(
        public_erp_form.cleaned_data.get("code_insee"),
        public_erp_form.cleaned_data.get("type"),
    )
    for result in results:
        result["exists"] = Erp.objects.find_by_source_id(
            result["source"], result["source_id"]
        )
    return results


@login_required
@reversion.views.create_revision()
def contrib_delete(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    if request.method == "POST":
        form = PublicErpDeleteForm(request.POST)
        if form.is_valid():
            erp.delete()
            messages.add_message(
                request, messages.SUCCESS, "L'établissement a été supprimé."
            )
            return redirect("mes_erps")
    else:
        form = PublicErpDeleteForm()
    return render(
        request,
        template_name="contrib/delete.html",
        context={"erp": erp, "form": form},
    )


@login_required
def contrib_start(request):  # noqa
    siret_search_error = None
    name_search_error = None
    name_search_results = None
    public_erp_results = None
    public_erp_search_error = None
    (siret_form, name_form, public_erp_form) = (
        PublicSiretSearchForm(),
        PublicEtablissementSearchForm(),
        PublicPublicErpSearchForm(),
    )
    if request.method == "POST":
        if request.POST.get("search_type") == "by-business":
            name_form = PublicEtablissementSearchForm(request.POST)
            if name_form.is_valid():
                try:
                    name_search_results = find_sirene_businesses(name_form)
                except RuntimeError as err:
                    name_search_error = str(err)
        elif request.POST.get("search_type") == "by-siret":
            siret_form = PublicSiretSearchForm(request.POST)
            if siret_form.is_valid():
                try:
                    siret_info = sirene.get_siret_info(siret_form.cleaned_data["siret"])
                    data = serializers.encode_provider_data(siret_info)
                    return redirect(reverse("contrib_admin_infos") + "?data=" + data)
                except RuntimeError as err:
                    siret_search_error = err
        elif request.POST.get("search_type") == "by-public-erp":
            public_erp_form = PublicPublicErpSearchForm(request.POST)
            if public_erp_form.is_valid():
                try:
                    public_erp_results = find_public_erps(public_erp_form)
                except RuntimeError as err:
                    public_erp_search_error = err
    return render(
        request,
        template_name="contrib/0-start.html",
        context={
            "step": 1,
            "nafs": naf.NAF,
            "name_form": name_form,
            "name_search_error": name_search_error,
            "name_search_results": name_search_results,
            "siret_form": siret_form,
            "siret_search_error": siret_search_error,
            "public_erp_form": public_erp_form,
            "public_erp_results": public_erp_results,
            "public_erp_types": public_erp.TYPES,
            "public_erp_search_error": public_erp_search_error,
        },
    )


@login_required
@reversion.views.create_revision()
def contrib_admin_infos(request):
    data = None
    data_error = None
    existing_matches = None
    if request.method == "POST":
        form = PublicErpAdminInfosForm(request.POST)
        if form.is_valid():
            existing_matches = Erp.objects.find_existing_matches(
                form.cleaned_data.get("nom"), form.cleaned_data.get("geom")
            )
            if len(existing_matches) == 0 or request.POST.get("force") == "1":
                erp = form.save(commit=False)
                erp.published = False
                erp.user = request.user
                erp.save()
                messages.add_message(
                    request, messages.SUCCESS, "Les données ont été enregistrées."
                )
                return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        encoded_data = request.GET.get("data")
        if encoded_data is not None:
            try:
                data = serializers.decode_provider_data(encoded_data)
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
            "existing_matches": existing_matches,
        },
    )


@login_required
@reversion.views.create_revision()
def contrib_edit_infos(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    if request.method == "POST":
        form = PublicErpEditInfosForm(
            request.POST, instance=erp, initial={"recevant_du_public": True}
        )
        if form.is_valid():
            erp = form.save()
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        form = PublicErpAdminInfosForm(
            instance=erp, initial={"recevant_du_public": True}
        )
    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={"step": 1, "erp": erp, "form": form, "has_data": False,},
    )


@login_required
@reversion.views.create_revision()
def contrib_localisation(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    if request.method == "POST":
        form = PublicLocalisationForm(request.POST)
        if form.is_valid():
            lat = form.cleaned_data.get("lat")
            lon = form.cleaned_data.get("lon")
            erp.geom = Point(x=lon, y=lat, srid=4326)
            erp.save()
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            action = request.POST.get("action")
            if action == "contribute":
                return redirect(erp.get_absolute_url())
            else:
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
    request,
    erp_slug,
    step,
    form_fields,
    template_name,
    redirect_route,
    prev_route=None,
    redirect_hash=None,
):
    "Traitement générique des requêtes sur les formulaires d'accessibilité"

    erp = get_object_or_404(Erp.objects.select_related("accessibilite"), slug=erp_slug,)
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
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            action = request.POST.get("action")
            if action == "contribute":
                hash = "#" + redirect_hash if redirect_hash else ""
                return redirect(erp.get_absolute_url() + hash)
            else:
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
            "prev_route": reverse(prev_route, kwargs={"erp_slug": erp.slug})
            if prev_route
            else None,
        },
    )


@login_required
@reversion.views.create_revision()
def contrib_transport(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        2,
        schema.get_section_fields(schema.SECTION_TRANSPORT),
        "contrib/3-transport.html",
        "contrib_stationnement",
        prev_route="contrib_localisation",
        redirect_hash=schema.SECTION_TRANSPORT,
    )


@login_required
@reversion.views.create_revision()
def contrib_stationnement(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        2,
        schema.get_section_fields(schema.SECTION_STATIONNEMENT),
        "contrib/4-stationnement.html",
        "contrib_exterieur",
        prev_route="contrib_transport",
        redirect_hash=schema.SECTION_STATIONNEMENT,
    )


@login_required
@reversion.views.create_revision()
def contrib_exterieur(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        3,
        schema.get_section_fields(schema.SECTION_CHEMINEMENT_EXT),
        "contrib/5-exterieur.html",
        "contrib_entree",
        prev_route="contrib_stationnement",
        redirect_hash=schema.SECTION_CHEMINEMENT_EXT,
    )


@login_required
@reversion.views.create_revision()
def contrib_entree(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        4,
        schema.get_section_fields(schema.SECTION_ENTREE),
        "contrib/6-entree.html",
        "contrib_accueil",
        prev_route="contrib_exterieur",
        redirect_hash=schema.SECTION_ENTREE,
    )


@login_required
@reversion.views.create_revision()
def contrib_accueil(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        5,
        schema.get_section_fields(schema.SECTION_ACCUEIL),
        "contrib/7-accueil.html",
        "contrib_sanitaires",
        prev_route="contrib_entree",
        redirect_hash=schema.SECTION_ACCUEIL,
    )


@login_required
@reversion.views.create_revision()
def contrib_sanitaires(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        6,
        schema.get_section_fields(schema.SECTION_SANITAIRES),
        "contrib/8-sanitaires.html",
        "contrib_labellisation",
        prev_route="contrib_accueil",
        redirect_hash=schema.SECTION_SANITAIRES,
    )


@login_required
@reversion.views.create_revision()
def contrib_labellisation(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        7,
        schema.get_section_fields(schema.SECTION_LABELS),
        "contrib/9-labellisation.html",
        "contrib_commentaire",
        prev_route="contrib_sanitaires",
        redirect_hash=schema.SECTION_LABELS,
    )


@login_required
@reversion.views.create_revision()
def contrib_commentaire(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        8,
        schema.get_section_fields(schema.SECTION_COMMENTAIRE),
        "contrib/10-commentaire.html",
        "contrib_publication",
        prev_route="contrib_labellisation",
        redirect_hash=schema.SECTION_COMMENTAIRE,
    )


@login_required
@reversion.views.create_revision()
def contrib_publication(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    accessibilite = erp.accessibilite if hasattr(erp, "accessibilite") else None
    initial = {
        "user_type": erp.user_type,
        "published": erp.published,
        "certif": erp.published,
    }
    empty_a11y = False
    if request.method == "POST":
        form = PublicPublicationForm(
            request.POST, instance=accessibilite, initial=initial
        )
        if form.is_valid():
            accessibilite = form.save()
            if not accessibilite.has_data() and form.cleaned_data.get(
                "published", False
            ):
                erp.published = False
                erp.save()
                empty_a11y = True
            else:
                erp.user_type = form.cleaned_data.get("user_type")
                erp.published = form.cleaned_data.get("published")
                erp = erp.save()
                messages.add_message(
                    request, messages.SUCCESS, "Les données ont été sauvegardées."
                )
                return redirect("mes_erps")
    else:
        form = PublicPublicationForm(instance=accessibilite, initial=initial)
    return render(
        request,
        template_name="contrib/11-publication.html",
        context={
            "step": 9,
            "erp": erp,
            "form": form,
            "empty_a11y": empty_a11y,
            "prev_route": reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug}),
        },
    )


@login_required
def contrib_claim(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user__isnull=True, published=True)
    if request.method == "POST":
        form = PublicClaimForm(request.POST)
        if form.is_valid():
            erp.user = request.user
            erp.save()
            messages.add_message(
                request, messages.SUCCESS, "L'établissement a été revendiqué."
            )
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        form = PublicClaimForm()
    return render(
        request, template_name="contrib/claim.html", context={"erp": erp, "form": form}
    )
