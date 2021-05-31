import datetime
import reversion

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, F, Q
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from django_registration.backends.activation.views import (
    ActivationView,
    RegistrationView,
)

from core import mailer

from erp.models import Accessibilite, Commune, Erp, Vote
from erp.provider import departements, search as provider_search

from erp import forms
from erp import schema
from erp import serializers
from erp import versioning
from subscription.models import ErpSubscription


def handler403(request, exception):
    return render(
        request,
        "403.html",
        context={"exception": exception},
        status=403,
    )


def handler404(request, exception):
    return render(
        request,
        "404.html",
        context={"exception": exception},
        status=404,
    )


def handler500(request):
    return render(request, "500.html", context={}, status=500)


def make_geojson(erp_qs):
    "Take an Erp queryset and serialize it to geojson."
    serializer = serializers.SpecialErpSerializer()
    return serializer.serialize(
        erp_qs,
        geometry_field="geom",
        use_natural_foreign_keys=True,
        fields=[
            "pk",
            "nom",
            "activite__nom",
            "activite__vector_icon",
            "adresse",
            "absolute_url",
            "has_accessibilite",
        ],
    )


def home(request):
    return render(request, "index.html")


def challenge_ddt(request):
    start_date = datetime.datetime(2021, 2, 22, 9)
    stop_date = datetime.datetime(2021, 3, 31, 23, 59, 59)
    today = datetime.datetime.today()
    filters = Q(
        erp__published=True,
        erp__accessibilite__isnull=False,
        erp__geom__isnull=False,
        erp__user__email__contains="rhone.gouv.fr",
        erp__created_at__gte=start_date,
        erp__created_at__lt=stop_date,
    )
    excludes = Q(erp__user__username="julien")
    top_contribs = (
        get_user_model()
        .objects.annotate(
            erp_count_published=Count(
                "erp",
                filter=filters,
                excude=excludes,
                distinct=True,
            )
        )
        .filter(filters)
        .exclude(excludes)
        .filter(erp_count_published__gt=0)
        .order_by("-erp_count_published")
    )
    return render(
        request,
        "challenge/podium.html",
        context={
            "start_date": start_date,
            "stop_date": stop_date,
            "today": today,
            "top_contribs": top_contribs,
        },
    )


def communes(request):
    communes_qs = Commune.objects.erp_stats()[:12]
    latest = (
        Erp.objects.select_related("activite", "commune_ext")
        .published()
        .order_by("-created_at")[:17]
    )
    return render(
        request,
        "communes.html",
        context={"communes": communes_qs, "latest": latest},
    )


def where(request):
    NB_COMMUNES_SUGG = 4
    NB_DPT_SUGG = 2
    results = []
    q = request.GET.get("q", "").strip()
    if q and len(q) > 0:
        communes_qs = (
            Commune.objects.search(q)
            .order_by(F("population").desc(nulls_last=True))
            .values(
                "code_insee",
                "nom",
                "departement",
            )
        )
        for commune in communes_qs[:NB_COMMUNES_SUGG]:
            results.append(
                {
                    "id": commune["code_insee"],
                    "text": f"{commune['nom']} ({commune['departement']})",
                }
            )
        results += departements.search(q, limit=NB_DPT_SUGG, for_autocomplete=True)
    return JsonResponse({"q": q, "results": results})


def get_where_data(where):
    if not where or where == "france_entiere":  # france entière
        return {"type": "france_entiere"}
    elif len(where) == 5:  # code insee
        return {"type": "commune", "obj": Commune.objects.get(code_insee=where)}
    elif len(where) == 2:  # departement
        return {"type": "departement", "obj": departements.get_departement(where)}
    return None


def search(request):
    where = request.GET.get("where", "")
    what = request.GET.get("what", "")
    search_where_label = request.GET.get("search_where_label", "")
    paginator = pager = None
    pager_base_url = None
    page_number = 1
    lat = None
    lon = None
    geojson_list = None
    if len(where) > 0 or len(what) > 0:
        erp_qs = Erp.objects.select_related(
            "accessibilite", "activite", "commune_ext"
        ).published()
        if what:
            erp_qs = erp_qs.search_what(what)
        if where:
            erp_qs = erp_qs.search_where(where)
        if where == "around_me":
            try:
                (lat, lon) = (
                    float(request.GET.get("lat")),
                    float(request.GET.get("lon")),
                )
                erp_qs = erp_qs.nearest((lat, lon), max_radius_km=20).order_by(
                    "distance"
                )
            except ValueError:
                pass
        paginator = Paginator(erp_qs, 10)
        page_number = request.GET.get("page", 1)
        pager = paginator.get_page(page_number)
        pager_base_url = (
            f"?where={where or ''}&what={what or ''}&lat={lat or ''}&lon={lon or ''}"
        )
        geojson_list = make_geojson(pager)
    return render(
        request,
        "search/results.html",
        context={
            "paginator": paginator,
            "pager": pager,
            "pager_base_url": pager_base_url,
            "page_number": page_number,
            "lat": request.GET.get("lat"),
            "lon": request.GET.get("lon"),
            "search_ongoing": where or what,
            "search_where": where,
            "search_what": what,
            "search_where_label": search_where_label,
            "where_data": get_where_data(where),
            "geojson_list": geojson_list,
            "commune_json": None,
            "around": None,  # XXX: (lat, lon)
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


class EditorialView(TemplateView):
    template_name = "editorial/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def erp_details(request, commune, erp_slug, activite_slug=None):
    base_qs = (
        Erp.objects.select_related(
            "accessibilite",
            "activite",
            "commune_ext",
            "user",
            "statuscheck",
        )
        .published()
        .with_votes()
        .filter(
            commune_ext__slug=commune,
            slug=erp_slug,
        )
    )
    if activite_slug:
        base_qs = base_qs.filter(activite__slug=activite_slug)
    erp = get_object_or_404(base_qs)
    nearest_erps = (
        Erp.objects.select_related("accessibilite", "activite", "commune_ext")
        .published()
        .nearest([erp.geom.coords[1], erp.geom.coords[0]])
        .filter(distance__lt=Distance(km=20))[:10]
    )
    geojson_list = make_geojson(nearest_erps)
    form = forms.ViewAccessibiliteForm(instance=erp.accessibilite)
    accessibilite_data = form.get_accessibilite_data()
    user_vote = (
        request.user.is_authenticated
        and Vote.objects.filter(user=request.user, erp=erp).first() is not None
    )
    user_is_subscribed = request.user.is_authenticated and erp.is_subscribed_by(
        request.user
    )
    return render(
        request,
        "erp/index.html",
        context={
            "accessibilite_data": accessibilite_data,
            "activite": erp.activite,
            "commune": erp.commune_ext,
            "commune_json": erp.commune_ext.toTemplateJson(),
            "erp": erp,
            "geojson_list": geojson_list,
            "nearest_erps": nearest_erps,
            "user_is_subscribed": user_is_subscribed,
            "user_vote": user_vote,
        },
    )


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
            messages.add_message(
                request, messages.SUCCESS, "Votre vote a été enregistré."
            )
    return redirect(erp.get_absolute_url())


@login_required
def mon_compte(request):
    return render(request, "compte/index.html")


@login_required
def mon_identifiant(request):
    if request.method == "POST":
        form = forms.UsernameChangeForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            user = get_user_model().objects.get(id=request.user.id)
            old_username = user.username
            user.username = username
            user.save()
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(user).pk,
                object_id=user.id,
                object_repr=username,
                action_flag=CHANGE,
                change_message=f"Changement de nom d'utilisateur (avant: {old_username})",
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                f"Votre nom d'utilisateur a été changé en {user.username}.",
            )
            return redirect("mon_identifiant")
    else:
        form = forms.UsernameChangeForm(initial={"username": request.user.username})
    return render(
        request,
        "compte/mon_identifiant.html",
        context={"form": form},
    )


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


@login_required
def mes_abonnements(request):
    qs = (
        ErpSubscription.objects.select_related(
            "erp", "erp__activite", "erp__commune_ext", "erp__user"
        )
        .filter(user=request.user)
        .order_by("-updated_at")
    )
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page", 1)
    pager = paginator.get_page(page_number)
    return render(
        request,
        "compte/mes_abonnements.html",
        context={"pager": pager, "pager_base_url": "?1"},
    )


@login_required
@reversion.views.create_revision()
def contrib_delete(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    if request.method == "POST":
        form = forms.PublicErpDeleteForm(request.POST)
        if form.is_valid():
            erp.delete()
            messages.add_message(
                request, messages.SUCCESS, "L'établissement a été supprimé."
            )
            return redirect("mes_erps")
    else:
        form = forms.PublicErpDeleteForm()
    return render(
        request,
        template_name="contrib/delete.html",
        context={"erp": erp, "form": form},
    )


@login_required
def contrib_start(request):
    form = forms.ProviderGlobalSearchForm(
        initial={"code_insee": request.GET.get("code_insee")}
    )
    return render(
        request,
        template_name="contrib/0-start.html",
        context={"step": 1, "form": form},
    )


@login_required
def contrib_global_search(request):
    results = error = None
    form = forms.ProviderGlobalSearchForm(request.GET if request.GET else None)
    if form.is_valid():
        try:
            results = provider_search.global_search(
                form.cleaned_data["search"],
                form.cleaned_data["code_insee"],
            )
        except RuntimeError as err:
            error = err
    return render(
        request,
        template_name="contrib/0a-search_results.html",
        context={
            "step": 1,
            "results": results,
            "form": form,
            "form_type": "global",
            "error": error,
        },
    )


@login_required
@reversion.views.create_revision()
def contrib_admin_infos(request):
    data = None
    data_error = None
    existing_matches = None
    if request.method == "POST":
        form = forms.PublicErpAdminInfosForm(request.POST)
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
        form = forms.PublicErpAdminInfosForm(data)
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
        form = forms.PublicErpEditInfosForm(
            request.POST, instance=erp, initial={"recevant_du_public": True}
        )
        if form.is_valid():
            erp = form.save()
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            return redirect("contrib_localisation", erp_slug=erp.slug)
    else:
        form = forms.PublicErpAdminInfosForm(
            instance=erp, initial={"recevant_du_public": True}
        )
    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "erp": erp,
            "form": form,
            "has_data": False,
        },
    )


@login_required
@reversion.views.create_revision()
def contrib_localisation(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    if request.method == "POST":
        form = forms.PublicLocalisationForm(request.POST)
        if form.is_valid():
            lat = form.cleaned_data.get("lat")
            lon = form.cleaned_data.get("lon")
            erp.geom = Point(x=lon, y=lat, srid=4326)
            erp.save()
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            return redirect("contrib_transport", erp_slug=erp.slug)
    elif erp.geom is not None:
        form = forms.PublicLocalisationForm(
            {"lon": erp.geom.coords[0], "lat": erp.geom.coords[1]}
        )
    return render(
        request,
        template_name="contrib/2-localisation.html",
        context={
            "step": 1,
            "erp": erp,
            "form": form,
        },
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

    erp = get_object_or_404(
        Erp.objects.select_related("accessibilite"),
        slug=erp_slug,
    )
    accessibilite = erp.accessibilite if hasattr(erp, "accessibilite") else None

    # N'amener l'utilisateur vers l'étape de publication que:
    # - s'il est propriétaire de la fiche
    # - ou s'il est à une étape antérieure à celle qui amène à la gestion de la publication
    user_can_access_next_route = request.user == erp.user or step != 8

    if request.method == "POST":
        Form = modelform_factory(
            Accessibilite, form=forms.AdminAccessibiliteForm, fields=form_fields
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
            if user_can_access_next_route:
                return redirect(
                    reverse(redirect_route, kwargs={"erp_slug": erp.slug}) + "#content"
                )
            else:
                redirect_url = erp.get_absolute_url()
                if step == 7:
                    redirect_url += f"#{redirect_hash}"
                return redirect(redirect_url)
    else:
        form = forms.AdminAccessibiliteForm(instance=accessibilite)

    if prev_route:
        prev_route = reverse(prev_route, kwargs={"erp_slug": erp.slug})
    else:
        prev_route = None

    if user_can_access_next_route:
        next_route = reverse(redirect_route, kwargs={"erp_slug": erp.slug})
    else:
        next_route = None

    return render(
        request,
        template_name=template_name,
        context={
            "step": step,
            "erp": erp,
            "form": form,
            "accessibilite": accessibilite,
            "redirect_hash": redirect_hash,
            "next_route": next_route,
            "prev_route": prev_route,
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
        "subscribe": erp.is_subscribed_by(request.user),
    }
    empty_a11y = False
    if request.method == "POST":
        form = forms.PublicPublicationForm(
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
                if form.cleaned_data.get("subscribe"):
                    ErpSubscription.subscribe(erp, request.user)
                else:
                    ErpSubscription.unsubscribe(erp, request.user)
                erp = erp.save()
                messages.add_message(
                    request, messages.SUCCESS, "Les données ont été sauvegardées."
                )
                return redirect("mes_erps")
    else:
        form = forms.PublicPublicationForm(instance=accessibilite, initial=initial)
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
    erp = Erp.objects.filter(slug=erp_slug, user__isnull=True, published=True).first()
    if not erp:
        erp = get_object_or_404(Erp, slug=erp_slug, published=True)
        return redirect("contrib_edit_infos", erp_slug=erp.slug)
    if request.method == "POST":
        form = forms.PublicClaimForm(request.POST)
        if form.is_valid():
            erp.user = request.user
            erp.user_type = Erp.USER_ROLE_GESTIONNAIRE
            erp.save()
            messages.add_message(
                request, messages.SUCCESS, "Opération effectuée avec succès."
            )
            return redirect("contrib_edit_infos", erp_slug=erp.slug)
    else:
        form = forms.PublicClaimForm()
    return render(
        request,
        template_name="contrib/claim.html",
        context={"erp": erp, "form": form},
    )


@login_required
def mapicons(request):
    mapicons = [
        "abseiling",
        "accounting",
        "airport",
        "amusement-park",
        "aquarium",
        "archery",
        "architect",
        "armurerie",
        "art-gallery",
        "assistive-listening-system",
        "athletisme",
        "atm",
        "audio-description",
        "baby",
        "bakery",
        "baignoire",
        "bank",
        "bar",
        "baseball",
        "beauty-salon",
        "beer",
        "bicycle-store",
        "bicycling",
        "boat-ramp",
        "boat-tour",
        "boating",
        "bonbon",
        "book-store",
        "bottle",
        "bowling-alley",
        "braille",
        "building",
        "bus-station",
        "cafe",
        "cake",
        "campground",
        "canoe",
        "car-dealer",
        "car-learn",
        "car-rental",
        "car-repair",
        "car-wash",
        "casino",
        "cemetery",
        "chairlift",
        "chapeau",
        "chaussure",
        "cheese",
        "church",
        "cinema",
        "circle",
        "city-hall",
        "climbing",
        "clock",
        "closed-captioning",
        "clothing-store",
        "coffee",
        "compass",
        "computer",
        "convenience-store",
        "courthouse",
        "cow",
        "cross-country-skiing",
        "crosshairs",
        "dentist",
        "department-store",
        "diving",
        "doctor",
        "electrician",
        "electronics-store",
        "embassy",
        "enfant",
        "estomac",
        "expand",
        "female",
        "finance",
        "fire-station",
        "fish-cleaning",
        "fishing-pier",
        "fishing",
        "flocon",
        "florist",
        "food",
        "fullscreen",
        "funeral-home",
        "furniture-store",
        "gas-station",
        "general-contractor",
        "golf",
        "grocery-or-supermarket",
        "gym",
        "hair-care",
        "hardware-store",
        "health",
        "hindu-temple",
        "horse-riding",
        "hospital",
        "hotel",
        "ice-fishing",
        "ice-skating",
        "inline-skating",
        "insurance-agency",
        "jet-skiing",
        "jewelry-store",
        "jouet",
        "kayaking",
        "labo",
        "laundry",
        "lawyer",
        "library",
        "liquor-store",
        "local-government",
        "location-arrow",
        "locksmith",
        "lodging",
        "low-vision-access",
        "male",
        "mairie",
        "makeup",
        "market",
        "marianne",
        "marina",
        "meat",
        "mosque",
        "motobike-trail",
        "movie-rental",
        "movie-theater",
        "moving-company",
        "museum",
        "musique",
        "natural-feature",
        "night-club",
        "office-tourisme",
        "open-captioning",
        "ophtalmo",
        "optique",
        "painter",
        "panier",
        "parfum",
        "park",
        "parking",
        "pet-store",
        "pharmacy",
        "physiotherapist",
        "place-of-worship",
        "playground",
        "plumber",
        "point-of-interest",
        "police",
        "political",
        "pompier",
        "post-box",
        "post-office",
        "projection",
        "rafting",
        "real-estate-agency",
        "restaurant",
        "roofing-contractor",
        "route-pin",
        "route",
        "rv-park",
        "sailing",
        "school",
        "scuba-diving",
        "search",
        "shield",
        "shopping-mall",
        "sign-language",
        "skateboarding",
        "ski-jumping",
        "skiing",
        "sledding",
        "snow-shoeing",
        "snowboarding",
        "snowmobile",
        "spa",
        "sport",
        "square-pin",
        "square-rounded",
        "square",
        "stadium",
        "storage",
        "store",
        "subway-station",
        "surfing",
        "swimming",
        "synagogue",
        "tabac",
        "taxi-stand",
        "telephonie",
        "tennis",
        "theatre",
        "toilet",
        "trail-walking",
        "train-station",
        "traiteur",
        "transit-station",
        "travel-agency",
        "trees",
        "unisex",
        "university",
        "veterinary-care",
        "vaccin",
        "vase",
        "vegetables",
        "viewing",
        "volume-control-telephone",
        "walking",
        "waterskiing",
        "whale-watching",
        "wheelchair",
        "wind-surfing",
        "zoo",
    ]
    return render(request, "mapicons.html", context={"mapicons": mapicons})


def contrib_documentation(request):
    return render(
        request,
        "contrib/documentation.html",
        context={"sections": schema.get_documentation_fieldsets()},
    )
