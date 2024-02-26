import datetime
import json
import re
import urllib
from decimal import Decimal
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as translate
from django.views.generic import TemplateView
from reversion.views import create_revision

from api.views import WidgetSerializer
from compte.signals import erp_claimed
from core.lib import geo, url
from core.mailer import BrevoMailer
from erp import forms, schema, serializers
from erp.forms import get_contrib_form_for_activity, get_vote_button_title
from erp.models import Accessibilite, Activite, ActivitySuggestion, Commune, Erp, Vote
from erp.provider import acceslibre
from erp.provider import search as provider_search
from erp.provider.search import filter_erps_by_equipments, get_equipments, get_equipments_shortcuts
from stats.models import Challenge
from stats.queries import get_active_contributors_ids
from subscription.models import ErpSubscription

HOURS = 60 * 60


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
    return serializers.SpecialErpSerializer().serialize(
        erp_qs,
        geometry_field="geom",
        use_natural_foreign_keys=True,
        fields=[
            "uuid",
            "nom",
            "activite__nom",
            "activite__vector_icon",
            "adresse",
            "absolute_url",
        ],
    )


def home(request):
    return render(
        request,
        "index.html",
        context={
            "erps": Erp.objects.published(),
            "contributors": get_active_contributors_ids(),
        },
    )


def challenges(request):
    today = datetime.datetime.today()
    challenges = Challenge.objects.filter(active=True)
    return render(
        request,
        "challenge/list.html",
        context={
            "today": today,
            "challenges": challenges,
            "challenges_en_cours": challenges.filter(start_date__lte=today, end_date__gt=today),
            "challenges_termines": challenges.filter(end_date__lt=today),
            "challenges_a_venir": challenges.filter(
                start_date__gt=today,
            ),
        },
    )


@login_required
def challenge_inscription(request, challenge_slug=None):
    challenge = get_object_or_404(Challenge, slug=challenge_slug)
    today = datetime.datetime.today()
    challenges = Challenge.objects.filter(
        Q(active=True)
        & (
            Q(
                start_date__gt=today,
            )
            | Q(start_date__lte=today, end_date__gt=today)
        )
    )
    if request.user.email in challenges.values_list("players__email", flat=True):
        messages.add_message(request, messages.ERROR, translate("Vous participez déjà à un autre challenge."))
    elif request.user not in challenge.players.all():
        challenge.players.add(request.user)
        messages.add_message(request, messages.SUCCESS, translate("Votre inscription a bien été enregistrée."))
    else:
        messages.add_message(request, messages.INFO, translate("Vous êtes déjà inscrit au challenge."))
    return redirect("challenges")


def challenge_ddt(request):
    today = datetime.datetime.today()
    challenge = Challenge.objects.get(slug="challenge-ddt")
    return render(
        request,
        "challenge/podium.html",
        context={
            "start_date": challenge.start_date,
            "stop_date": challenge.end_date,
            "today": today,
            "top_contribs": challenge.classement,
            "total_contributions": challenge.nb_erp_total_added,
        },
    )


def challenge_detail(request, challenge_slug=None):
    challenge = get_object_or_404(Challenge, slug=challenge_slug)
    today = datetime.datetime.today()
    return render(
        request,
        "challenge/detail.html",
        context={
            "challenge": challenge,
            "start_date": challenge.start_date,
            "stop_date": challenge.end_date,
            "today": today,
            "top_contribs": challenge.classement,
            "total_contributions": challenge.nb_erp_total_added,
        },
    )


def communes(request):
    communes_qs = Commune.objects.erp_stats().only("nom", "slug", "departement", "geom")[:12]
    latest = Erp.objects.select_related("activite", "commune_ext").published().order_by("-id")[:17]
    return render(
        request,
        "communes.html",
        context={"communes": communes_qs, "latest": latest},
    )


def _search_commune_code_postal(qs, code_insee):
    commune = None
    if code_insee:
        commune = Commune.objects.filter(code_insee=code_insee).first()
    return (
        commune,
        qs.in_code_postal(commune) if commune else qs,
    )


def _cleaned_search_params_as_dict(get_parameters):
    allow_list = ("where", "what", "lat", "lon", "code", "search_type", "postcode", "street_name", "municipality")
    cleaned_dict = {
        k: "" if get_parameters.get(k, "") == "None" else get_parameters.get(k, "")
        for k, v in get_parameters.items()
        if k in allow_list
    }
    cleaned_dict["where"] = cleaned_dict.get("where") or "France entière"
    return cleaned_dict


def _clean_address(where):
    """
    where is a string as returned by geoloc API on frontend side. It returns city and code_departement, this is pure string
    work, nothing coming from a database or elsewhere.
    For ex:
        "Paris (75006)" returns ("Paris", "75")
        "Lille (59)" returns ("Lille", "59")
        "Strasbourg" returns ("Strasbourg", "")
        "10 Rue Marin 69160 Tassin-la-Demi-Lune" returns ("Tassin-la-Demi-Lune", "")
    """
    where = (where or "()").strip()

    # remove code departement in where
    address = re.split(r"\(|\)", where)
    city = where
    code_departement = ""
    if len(address) >= 2:
        city = address[0].strip()
        code_departement = address[1]
    elif found := re.search(r".* [0-9]{5} (.*)", where):
        city = found.groups(1)[0]
    return city, code_departement


def _parse_location_or_404(lat, lon):
    if not lat or not lon:
        return None
    try:
        return geo.parse_location((lat, lon))
    except RuntimeError as err:
        raise Http404(err)


def _filter_erp_by_location(queryset, **kwargs):
    search_type = kwargs.get("search_type")
    lat, lon = kwargs.get("lat"), kwargs.get("lon")
    location = _parse_location_or_404(lat, lon)
    postcode = kwargs.get("postcode")

    if search_type == settings.IN_MUNICIPALITY_SEARCH_TYPE:
        return queryset.filter(commune=kwargs.get("municipality").nom)

    if search_type == settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_CITY:
        city, code_departement = _clean_address(kwargs.get("where"))
        return queryset.filter(commune__iexact=city, code_postal__startswith=code_departement)

    if search_type in (settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_HOUSENUMBER, "Autour de moi", translate("Autour de moi")):
        return queryset.nearest(location, max_radius_km=0.2)

    if search_type == settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_STREET:
        street_name = kwargs.get("street_name")
        return queryset.filter(code_postal=postcode, voie__icontains=street_name)
    return queryset


def _get_or_create_api_key():
    api_key = cache.get(settings.INTERNAL_API_KEY_NAME)
    if api_key:
        return api_key

    api_key = User.objects.make_random_password(32)
    cache.set(settings.INTERNAL_API_KEY_NAME, api_key, timeout=1 * HOURS)
    return api_key


def search(request):
    filters = _cleaned_search_params_as_dict(request.GET)
    base_queryset = Erp.objects.published().with_activity()
    base_queryset = base_queryset.search_what(filters.get("what"))
    queryset = _filter_erp_by_location(base_queryset, **filters)
    queryset = filter_erps_by_equipments(queryset, request.GET.getlist("equipments", []))
    zoom_level = settings.MAP_DEFAULT_ZOOM
    if request.GET.get("municipality"):
        municipality = Commune.objects.filter(nom=request.GET["municipality"]).first()
        if municipality:
            zoom_level = municipality.get_zoom()
    elif request.GET.get("search_type") in ("street", "locality"):
        zoom_level = settings.MAP_DEFAULT_ZOOM_STREET
    elif request.GET.get("search_type") == "housenumber":
        zoom_level = settings.MAP_DEFAULT_ZOOM_HOUSENUMBER

    paginator = Paginator(queryset, 50)
    pager = paginator.get_page(request.GET.get("page") or 1)
    pager_base_url = url.encode_qs(**filters)

    context = {
        **filters,
        "pager": pager,
        "pager_base_url": pager_base_url,
        "paginator": paginator,
        "map_api_key": _get_or_create_api_key(),
        "dynamic_map": True,
        "equipments_shortcuts": get_equipments_shortcuts(),
        "equipments": get_equipments(),
        "zoom_level": zoom_level,
        "geojson_list": make_geojson(pager),
    }
    return render(request, "search/results.html", context=context)


def search_in_municipality(request, commune_slug):
    municipality = get_object_or_404(Commune, slug=commune_slug)
    filters = _cleaned_search_params_as_dict(request.GET)
    filters["search_type"] = settings.IN_MUNICIPALITY_SEARCH_TYPE
    filters["municipality"] = municipality
    base_queryset = Erp.objects.published().with_activity()
    base_queryset = base_queryset.search_what(filters.get("what"))
    queryset = _filter_erp_by_location(base_queryset, **filters)

    paginator = Paginator(queryset, 10)
    pager = paginator.get_page(request.GET.get("page") or 1)

    context = {
        **filters,
        "pager": pager,
        "pager_base_url": url.encode_qs(**filters),
        "paginator": paginator,
        "where": str(municipality),
        "commune": municipality,
        "commune_json": municipality.toTemplateJson(),
        "geojson_list": make_geojson(pager),
        "search_type": settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_CITY,
        "municipality": municipality.nom,
    }
    return render(request, "search/results.html", context=context)


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
            "user",
        )
        .published()
        .with_votes()
        .filter(slug=erp_slug)
    )

    erp = get_object_or_404(base_qs)

    need_redirect = False
    if erp.commune_ext and not (commune in erp.commune_ext.slug or erp.commune_ext.slug in commune):
        # NOTE: the last 2 conditions are here to manage "arrondissements" in commune ext
        need_redirect = True

    if activite_slug and (erp.activite.slug != activite_slug):
        need_redirect = True

    # NOTE: ATM we won't have this case as we fetch the erp from its slug. But the aim is to fetch it by its id/uuid
    if erp_slug != erp.slug:
        need_redirect = True

    if need_redirect:
        return redirect(erp.get_absolute_url())

    # translate free texts if user is not displaying the page in french
    current_language = get_language()
    if current_language != "fr":
        erp.translate(current_language)

    form = forms.ViewAccessibiliteForm(instance=erp.accessibilite)
    accessibilite_data = form.get_accessibilite_data()
    is_authenticated = request.user.is_authenticated
    is_user_erp_owner = request.user == erp.user
    user_has_rights_to_vote = is_authenticated and not is_user_erp_owner
    current_vote = None
    if is_authenticated:
        current_vote = Vote.objects.filter(user=request.user, erp=erp).first()
    has_vote = current_vote is not None
    vote_up_form = {
        "title": get_vote_button_title(is_authenticated, is_user_erp_owner, has_vote, default="Oui"),
        "value": Vote.UNVOTE_UP_ACTION if has_vote and current_vote.is_positive else Vote.VOTE_UP_ACTION,
        "count": getattr(erp, "count_positives", 0),
        "user_can_vote": user_has_rights_to_vote and (not has_vote or current_vote.is_positive),
    }
    vote_down_form = {
        "title": get_vote_button_title(is_authenticated, is_user_erp_owner, has_vote, default="Non"),
        "value": Vote.UNVOTE_DOWN_ACTION if has_vote and current_vote.is_negative else Vote.VOTE_DOWN_ACTION,
        "count": getattr(erp, "count_negatives", 0),
        "user_can_vote": user_has_rights_to_vote and (not has_vote or current_vote.is_negative),
        "toogle_form": not has_vote,
        "type": "button" if not has_vote else "submit",
    }

    user_is_subscribed = request.user.is_authenticated and erp.is_subscribed_by(request.user)
    url_widget_js = f"{settings.SITE_ROOT_URL}/static/js/widget.js"

    has_th = bool(schema.LABEL_TH in (erp.accessibilite.labels or []))
    th_labels = []
    if has_th:
        th_labels = [
            value for key, value in schema.HANDICAP_CHOICES if key in erp.accessibilite.labels_familles_handicap
        ]

    # NOTE: if the widget code is edited it should be also reflected in metabase
    widget_tag = f"""<div id="widget-a11y-container" data-pk="{erp.uuid}" data-baseurl="{settings.SITE_ROOT_URL}"></div>\n
<a href="#" aria-haspopup="dialog" data-erp-pk="{erp.uuid}" aria-controls="dialog">{translate('Accessibilité')}</a>
<script src="{url_widget_js}" type="text/javascript" async="true"></script>"""
    return render(
        request,
        "erp/index.html",
        context={
            "accessibilite_data": accessibilite_data,
            "activite": erp.activite,
            "commune": erp.commune_ext,
            "commune_json": erp.commune_ext.toTemplateJson() if erp.commune_ext else None,
            "erp": erp,
            "geojson_list": make_geojson([erp]),
            "widget_tag": widget_tag,
            "url_widget_js": url_widget_js,
            "root_url": settings.SITE_ROOT_URL,
            "user_is_subscribed": user_is_subscribed,
            "vote_up_form": vote_up_form,
            "vote_down_form": vote_down_form,
            "th_labels": th_labels,
            "has_th": has_th,
            "map_options": json.dumps(
                {
                    "scrollWheelZoom": False,
                    "dragging": False,
                }
            ),
        },
    )


def from_uuid(request, uuid):
    erp = get_object_or_404(Erp.objects.published(), uuid=uuid)
    return redirect(erp.get_absolute_url())


def widget_from_uuid(request, uuid):
    def _render_404():
        return render(
            request, "erp/widget/404.html", context={"ref_uuid": uuid, "base_url": f"{settings.SITE_ROOT_URL}"}
        )

    try:
        UUID(uuid)
    except ValueError:
        return _render_404()

    # activite is used in template when get_absolute_uri
    erp = Erp.objects.select_related("accessibilite", "activite").published().filter(uuid=uuid).first()

    if not erp:
        return _render_404()

    access_sections = WidgetSerializer(erp).data["sections"]
    access_data = {}
    for entry in access_sections:
        access_data[entry["title"]] = {"label": " \n ".join(entry["labels"]), "icon": entry["icon"]}

    return render(
        request,
        "erp/widget/index.html",
        context={
            "ref_uuid": erp.uuid,
            "accessibilite_data": access_data,
            "erp": erp,
            "base_url": f"{settings.SITE_ROOT_URL}",
        },
    )


@login_required
def vote(request, erp_slug):
    if not request.user.is_active:
        raise Http404(translate("Seuls les utilisateurs actifs peuvent voter."))
    erp = get_object_or_404(Erp, slug=erp_slug, published=True)
    if request.user == erp.user:
        return HttpResponseBadRequest(translate("Vous ne pouvez pas voter sur votre établissement"))
    if not request.method == "POST":
        return redirect(erp.get_absolute_url())

    action = request.POST.get("action")
    comment = request.POST.get("comment") if action == Vote.VOTE_DOWN_ACTION else None
    vote = erp.vote(request.user, action, comment=comment)
    if not vote:
        messages.add_message(request, messages.SUCCESS, translate("Votre vote a bien été effacé."))
        return redirect(erp.get_absolute_url())

    if vote.is_negative:
        route = reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug})
        context = {"erp_contrib_url": f"{settings.SITE_ROOT_URL}{route}"}
        BrevoMailer().send_email(to_list=request.user.email, template="vote_down", context=context)
        context = {
            "username": request.user.username,
            "erp_nom": erp.nom,
            "erp_absolute_url": erp.get_absolute_url(),
            "comment": comment,
            "user_email": request.user.email,
        }
        BrevoMailer().send_email(to_list=settings.DEFAULT_EMAIL, template="vote_down_admin", context=context)
    messages.add_message(request, messages.SUCCESS, translate("Votre vote a été enregistré."))
    return redirect(erp.get_absolute_url())


@login_required
@create_revision(request_creates_revision=lambda x: True)
def contrib_delete(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug, user=request.user)
    if request.method == "POST":
        form = forms.PublicErpDeleteForm(request.POST)
        if form.is_valid():
            erp.delete()
            messages.add_message(request, messages.SUCCESS, translate("L'établissement a été supprimé."))
            return redirect("mes_erps")
    else:
        form = forms.PublicErpDeleteForm()
    return render(
        request,
        template_name="contrib/delete.html",
        context={"erp": erp, "form": form},
    )


def contrib_start(request):
    form = forms.ProviderGlobalSearchForm(request.GET or None)
    if form.is_valid():
        return redirect(f"{reverse('contrib_global_search')}?{urllib.parse.urlencode(form.cleaned_data)}")

    return render(
        request,
        template_name="contrib/0-start.html",
        context={
            "form": form,
            "step": 0,
        },
    )


def contrib_global_search(request):
    results = error = None
    commune = ""
    results_bdd = []
    results = []

    need_external_api_search = True
    if request.GET.get("search_type") in ("housenumber", "street"):
        # Business rule: we do not want to search in external API if the user is providing a full address. We are
        # assuming he knows what he does and does not need help with some external API results.
        need_external_api_search = False

    activite = None
    if request.GET.get("activite"):
        activite = Activite.objects.filter(nom=request.GET.get("activite")).first()

    if request.GET.get("what"):
        what_lower = request.GET.get("what", "").lower()
        try:
            if need_external_api_search:
                results = provider_search.global_search(
                    what_lower,
                    request.GET.get("code"),
                    activity=activite,
                )
        except RuntimeError as err:
            error = err

        qs_results_bdd = (
            Erp.objects.select_related("accessibilite", "activite", "commune_ext").published().search_what(what_lower)
        )
        if activite:
            qs_results_bdd = qs_results_bdd.filter(activite=activite)

        commune, qs_results_bdd = _search_commune_code_postal(qs_results_bdd, request.GET.get("code"))
        results_bdd, results = acceslibre.parse_etablissements(qs_results_bdd, results)

    city, _ = _clean_address(request.GET.get("where"))

    return render(
        request,
        template_name="contrib/0a-search_results.html",
        context={
            "form": forms.ProviderGlobalSearchForm(initial=request.GET.copy()),
            "commune_search": commune,
            "step": 1,
            "next_step_title": schema.SECTION_TRANSPORT,
            "results_bdd": results_bdd,
            "results": results,
            "error": error,
            "results_global_count": len(results) + len(results_bdd),
            "query": {
                "nom": request.GET.get("what"),
                "commune": city,
                "lat": request.GET.get("lat"),
                "lon": request.GET.get("lon"),
                "activite": activite.pk if activite else None,
                "activite_slug": activite.slug if activite else None,
                "new_activity": request.GET.get("new_activity"),
                "code_postal": request.GET.get("postcode"),
            },
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_admin_infos(request):
    data = erp = external_erp = None
    data_error = None
    existing_matches = None
    duplicated = False
    if request.method == "POST":
        form = forms.PublicErpAdminInfosForm(request.POST, ignore_duplicate_check=request.POST.get("force") == "1")
        if form.is_valid():
            existing_matches = Erp.objects.find_existing_matches(
                form.cleaned_data.get("nom"), form.cleaned_data.get("geom")
            ).with_activity()
            if not existing_matches or request.POST.get("force") == "1":
                erp = form.save(commit=False)
                erp.published = False
                activite = form.cleaned_data.get("activite")
                erp.activite = activite
                erp.save(editor=request.user if request.user.is_authenticated else None)
                if erp.has_miscellaneous_activity:
                    ActivitySuggestion.objects.create(
                        name=form.cleaned_data["nouvelle_activite"],
                        erp=erp,
                        user=request.user if request.user.is_authenticated else None,
                    )
                messages.add_message(request, messages.SUCCESS, translate("Les données ont été enregistrées."))
                return redirect("contrib_a_propos", erp_slug=erp.slug)
        else:
            error_message = (form.errors.get("__all__", [""])[0] or "").lower()
            duplicated = bool("existe déjà" in error_message or translate("existe déjà") in error_message)
    else:
        encoded_data = request.GET.get("data")
        try:
            data = serializers.decode_provider_data(encoded_data)
        except RuntimeError as err:
            data_error = err
        else:
            data_erp = data.copy()
            try:
                if "activite_slug" in data:
                    data_erp["activite"] = data["activite"] = Activite.objects.get(slug=data["activite_slug"])
            except Activite.DoesNotExist:
                pass

            data["nouvelle_activite"] = data_erp.pop("new_activity", "")
            data_erp.pop("activite_slug", None)
            data_erp.pop("coordonnees", None)
            data_erp.pop("naf", None)
            data_erp.pop("lat", None)
            data_erp.pop("lon", None)
            external_erp = Erp(**data_erp)
        form = forms.PublicErpAdminInfosForm(initial=data)

    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "next_step_title": schema.SECTION_A_PROPOS,
            "form": form,
            "data_error": data_error,
            "existing_matches": existing_matches,
            "erp": erp,
            "external_erp": external_erp,
            "other_activity": Activite.objects.only("id").get(slug=Activite.SLUG_MISCELLANEOUS),
            "duplicated": duplicated,
            "map_options": json.dumps(
                {
                    "scrollWheelZoom": False,  # Zoom in/out is not permitted in contrib mode as it would result into a position change of the cross
                }
            ),
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_edit_infos(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    initial = {"lat": Decimal(erp.geom.y), "lon": Decimal(erp.geom.x)}
    if request.user.is_authenticated and erp.user is request.user:
        libelle_next = schema.SECTION_A_PROPOS
        next_route = schema.SECTIONS[schema.SECTION_A_PROPOS]["edit_route"]
    else:
        libelle_next = schema.SECTION_TRANSPORT
        next_route = schema.SECTIONS[schema.SECTION_TRANSPORT]["edit_route"]

    if request.method == "POST":
        form = forms.PublicErpEditInfosForm(request.POST, instance=erp, initial=initial)
        if form.is_valid():
            if not form.has_changed():
                return redirect(next_route, erp_slug=erp.slug)

            erp = form.save(commit=False)
            activite = form.cleaned_data.get("activite")
            erp.activite = activite
            erp.save(editor=request.user if request.user.is_authenticated else None)

            if erp.has_miscellaneous_activity:
                ActivitySuggestion.objects.create(
                    name=form.cleaned_data["nouvelle_activite"],
                    erp=erp,
                    user=request.user if request.user.is_authenticated else None,
                )
            messages.add_message(
                request,
                messages.SUCCESS,
                translate("Les données ont été enregistrées."),
            )
            return redirect(next_route, erp_slug=erp.slug)
    else:
        form = forms.PublicErpAdminInfosForm(instance=erp, initial=initial)

    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "next_step_title": libelle_next,
            "erp": erp,
            "form": form,
            "other_activity": Activite.objects.only("id").get(slug="autre"),
            # Zoom in/out is not permitted in edit mode as it would result into a position change of the cross
            "map_options": json.dumps({"scrollWheelZoom": False}),
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_a_propos(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    initial = {"user_type": erp.user_type or Erp.USER_ROLE_PUBLIC}
    if request.method == "POST":
        if erp.has_accessibilite():
            accessibilite = erp.accessibilite
        else:
            accessibilite = None
        form = forms.PublicAProposForm(request.POST, instance=accessibilite, initial=initial)
        if form.is_valid():
            erp.user_type = form.data["user_type"]
            accessibilite = form.save(commit=False)
            accessibilite.erp = erp
            accessibilite.save()

            erp.save(editor=request.user if request.user.is_authenticated else None)
            messages.add_message(
                request,
                messages.SUCCESS,
                translate("Les données ont été enregistrées."),
            )
            return redirect("contrib_transport", erp_slug=erp.slug)
    else:
        if hasattr(erp, "accessibilite"):
            form = forms.PublicAProposForm(instance=erp.accessibilite, initial=initial)
        else:
            form = forms.PublicAProposForm(instance=erp, initial=initial)
    return render(
        request,
        template_name="contrib/2-a-propos.html",
        context={
            "step": 2,
            "prev_route": reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
            "next_step_title": schema.SECTION_TRANSPORT,
            "erp": erp,
            "form": form,
        },
    )


def check_authentication(request, erp, form, check_online=True):
    redirect_path = redirect(
        reverse("login")
        + "?"
        + urllib.parse.urlencode({"next": request.path + "?" + urllib.parse.urlencode(form.data)})
    )
    if check_online:
        if erp.published and not request.user.is_authenticated:
            return redirect_path
    else:
        if not request.user.is_authenticated:
            return redirect_path


def process_accessibilite_form(
    request,
    erp_slug,
    step,
    form_fields,
    template_name,
    redirect_route,
    prev_route=None,
    next_step_title=None,
):
    """
    Traitement générique des requêtes sur les formulaires d'accessibilité
    """

    erp = get_object_or_404(
        Erp.objects.select_related("accessibilite"),
        slug=erp_slug,
    )
    accessibilite = erp.accessibilite if hasattr(erp, "accessibilite") else None

    contrib_form = get_contrib_form_for_activity(erp.activite)
    Form = modelform_factory(Accessibilite, form=contrib_form, fields=form_fields)

    if request.method == "POST":
        form = Form(request.POST, instance=accessibilite, user=request.user)
    else:
        if request.GET:
            form = Form(request.GET, instance=accessibilite, user=request.user)
        else:
            form = contrib_form(instance=accessibilite, initial={"entree_porte_presence": True}, user=request.user)
    if form.is_valid():
        if check_authentication(request, erp, form):
            return check_authentication(request, erp, form)
        accessibilite = form.save(commit=False)
        accessibilite.erp = erp
        accessibilite.save()
        if request.user.is_authenticated and accessibilite.erp.user is None:
            accessibilite.erp.user = request.user
            accessibilite.erp.save()
        form.save_m2m()
        if "publier" in request.POST:
            return redirect(reverse("contrib_publication", kwargs={"erp_slug": erp.slug}))

        messages.add_message(request, messages.SUCCESS, translate("Les données ont été enregistrées."))
        return redirect(reverse(redirect_route, kwargs={"erp_slug": erp.slug}) + "#content")

    if prev_route:
        prev_route = reverse(prev_route, kwargs={"erp_slug": erp.slug})
    else:
        prev_route = None

    return render(
        request,
        template_name=template_name,
        context={
            "step": step,
            "next_step_title": next_step_title,
            "erp": erp,
            "form": form,
            "accessibilite": accessibilite,
            "publier_route": reverse("contrib_publication", kwargs={"erp_slug": erp.slug}),
            "prev_route": prev_route,
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_transport(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    if request.user.is_authenticated and erp.user is request.user:
        prev_route = schema.SECTIONS[schema.SECTION_A_PROPOS]["edit_route"]
    else:
        prev_route = "contrib_edit_infos"

    return process_accessibilite_form(
        request,
        erp_slug,
        3,
        schema.get_section_fields(schema.SECTION_TRANSPORT),
        "contrib/3-transport.html",
        "contrib_exterieur",
        prev_route=prev_route,
        next_step_title=schema.SECTION_CHEMINEMENT_EXT,
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_exterieur(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        4,
        schema.get_section_fields(schema.SECTION_CHEMINEMENT_EXT),
        "contrib/4-exterieur.html",
        "contrib_entree",
        prev_route="contrib_transport",
        next_step_title=schema.SECTION_ENTREE,
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_entree(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        5,
        schema.get_section_fields(schema.SECTION_ENTREE),
        "contrib/5-entree.html",
        "contrib_accueil",
        prev_route="contrib_exterieur",
        next_step_title=schema.SECTION_ACCUEIL,
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_accueil(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        6,
        schema.get_section_fields(schema.SECTION_ACCUEIL),
        "contrib/6-accueil.html",
        "contrib_commentaire",
        prev_route="contrib_entree",
        next_step_title=schema.SECTION_COMMENTAIRE,
    )


def ensure_min_nb_answers(request, erp):
    if erp.published:
        return True

    # check that we have 4 root answers min, on contrib mode only (not on edit mode).
    form_fields = get_contrib_form_for_activity(erp.activite).base_fields.keys()
    root_fields = [field for field in form_fields if schema.FIELDS.get(field, {}).get("root") is True]

    nb_filled_in_fields = 0
    for attr in root_fields:
        # NOTE: we can not use bool() here, as False is a filled in info
        if getattr(erp.accessibilite, attr) not in (None, [], ""):
            nb_filled_in_fields += 1

    if nb_filled_in_fields >= settings.MIN_NB_ANSWERS_IN_CONTRIB:
        return True

    messages.add_message(
        request,
        messages.ERROR,
        translate("Vous n'avez pas fourni assez d'infos d'accessibilité. Votre établissement ne peut pas être publié."),
    )
    return False


@create_revision(request_creates_revision=lambda x: True)
def contrib_commentaire(request, erp_slug):
    return process_accessibilite_form(
        request,
        erp_slug,
        7,
        schema.get_section_fields(schema.SECTION_COMMENTAIRE),
        "contrib/7-commentaire.html",
        "contrib_publication",
        prev_route="contrib_accueil",
        next_step_title=None,
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_publication(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    if not ensure_min_nb_answers(request, erp):
        return redirect(request.META.get("HTTP_REFERER", reverse("contrib_commentaire", kwargs={"erp_slug": erp.slug})))

    if request.method == "POST":
        form = forms.PublicPublicationForm(request.POST, instance=erp)
    else:
        form = forms.PublicPublicationForm(request.GET or {"published": True}, instance=erp)

    if form.is_valid():
        if check_auth := check_authentication(request, erp, form, check_online=False):
            return check_auth

        erp = form.save()
        if erp.user is None:
            erp.user = request.user
            erp.save()

        ErpSubscription.subscribe(erp, erp.user)
        messages.add_message(request, messages.SUCCESS, translate("Les données ont été sauvegardées."))
        if erp.published:
            # Suppress old draft matching this ERP + send email notification
            for draft in Erp.objects.find_duplicate(
                numero=erp.numero,
                commune=erp.commune,
                activite=erp.activite,
                voie=erp.voie,
                lieu_dit=erp.lieu_dit,
                published=False,
            ).all():
                if not draft.user:
                    continue

                context = {"draft_nom": draft.nom, "commune": draft.commune, "erp_url": erp.get_absolute_uri()}
                BrevoMailer().send_email(to_list=draft.user.email, template="draft_deleted", context=context)
                draft.delete()

            redirect_url = erp.get_success_url()
        elif erp.user == request.user:
            redirect_url = reverse("mes_erps")
        else:
            redirect_url = reverse("mes_contributions")

        return redirect(redirect_url)

    return render(
        request,
        template_name="contrib/8-publication.html",
        context={
            "step": 8,
            "next_step_title": None,
            "erp": erp,
            "form": form,
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
        if form.is_valid() and form.cleaned_data["ok"] is True:
            erp.user = request.user
            erp.user_type = Erp.USER_ROLE_GESTIONNAIRE
            erp.save()
            erp_claimed.send(sender=Erp, instance=erp)
            messages.add_message(request, messages.SUCCESS, translate("Opération effectuée avec succès."))
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
