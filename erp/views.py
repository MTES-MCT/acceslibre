import datetime
import urllib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.measure import Distance
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from reversion.views import create_revision

from core import mailer
from core.lib import geo, url
from erp import forms, schema, serializers
from erp.export.utils import map_list_from_schema
from erp.models import Accessibilite, Activite, Commune, Erp, Vote
from erp.provider import acceslibre, geocoder
from erp.provider import search as provider_search
from stats.models import Challenge
from stats.queries import get_count_active_contributors
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
    return render(
        request,
        "index.html",
        context={
            "erp_count": Erp.objects.published().count(),
            "contributor_count": get_count_active_contributors(),
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
            "challenges_en_cours": challenges.filter(
                start_date__lte=today, end_date__gt=today
            ),
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
        messages.add_message(
            request, messages.ERROR, "Vous participez déjà à un autre challenge."
        )
    elif request.user not in challenge.players.all():
        challenge.players.add(request.user)
        messages.add_message(
            request, messages.SUCCESS, "Votre inscription a bien été enregistrée."
        )
    else:
        messages.add_message(
            request, messages.INFO, "Vous êtes déjà inscrit au challenge."
        )
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
    communes_qs = Commune.objects.erp_stats().only(
        "nom", "slug", "departement", "geom"
    )[:12]
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


def _search_commune_code_postal(qs, code_insee):
    commune = None
    if code_insee:
        commune = Commune.objects.filter(code_insee=code_insee).first()
    return (
        commune,
        qs.in_code_postal(commune) if commune else qs,
    )


def _search_commune_around(qs, point, code_insee):
    commune = None
    if code_insee:
        commune = Commune.objects.filter(code_insee=code_insee).first()
    return (
        commune,
        qs.in_and_around_commune(point, commune) if commune else qs.nearest(point),
    )


def _update_search_pager(pager, commune):
    for erp in pager.object_list:
        if any(
            [
                commune.contour and not commune.contour.covers(erp.geom),
                erp.code_postal not in commune.code_postaux,
            ]
        ):
            erp.outside = True
            break
    return pager


def _clean_search_params(params, *args):
    return (
        "" if params.get(arg, "") == "None" else params.get(arg, "") for arg in args
    )


def _parse_location_or_404(lat, lon):
    if not lat or not lon:
        return None
    try:
        return geo.parse_location((lat, lon))
    except RuntimeError as err:
        raise Http404(err)


def search(request, commune_slug=None):
    where, what, lat, lon, code = _clean_search_params(
        request.GET, "where", "what", "lat", "lon", "code"
    )
    where = where or "France entière"
    location = _parse_location_or_404(lat, lon)
    qs = (
        Erp.objects.select_related("accessibilite", "activite", "commune_ext")
        .published()
        .search_what(what)
    )
    commune = None
    if commune_slug:
        commune = get_object_or_404(Commune, slug=commune_slug)
        qs = qs.filter(commune_ext=commune)
        where = str(commune)
    elif location:
        commune, qs = _search_commune_around(qs, location, code)
    elif where and not where == "France entière":
        location = geocoder.autocomplete(where)
        if location:
            lat, lon = (location.y, location.x)  # update current searched lat/lon
            qs = qs.nearest(location)
        else:
            qs = qs.search_commune(where)
    # pager
    paginator = Paginator(qs, 10)
    pager = paginator.get_page(request.GET.get("page", 1))
    if commune:
        pager = _update_search_pager(pager, commune)
    pager_base_url = url.encode_qs(where=where, what=what, lat=lat, lon=lon, code=code)
    geojson_list = make_geojson(pager)
    return render(
        request,
        "search/results.html",
        context={
            "url_params": request.META["QUERY_STRING"],
            "commune": commune,
            "paginator": paginator,
            "pager": pager,
            "pager_base_url": pager_base_url,
            "lat": lat,
            "lon": lon,
            "code": code,
            "what": what,
            "where": where,
            "geojson_list": geojson_list,
            "commune_json": commune.toTemplateJson() if commune else None,
            "data_contrib": {
                "nom": what,
                "lat": lat,
                "lon": lon,
                "activite": "",
                "commune": commune.nom if commune else "",
            },
        },
    )


def global_map(request, commune_slug=None):
    where, what, lat, lon, code = _clean_search_params(
        request.GET, "where", "what", "lat", "lon", "code"
    )
    where = where or "France entière"
    location = _parse_location_or_404(lat, lon)
    qs = (
        Erp.objects.select_related("accessibilite", "activite", "commune_ext")
        .published()
        .search_what(what)
    )
    commune = None
    if commune_slug:
        commune = get_object_or_404(Commune, slug=commune_slug)
        qs = qs.filter(commune_ext=commune)
        where = str(commune)
    elif location:
        commune, qs = _search_commune_around(qs, location, code)
    elif where and not where == "France entière":
        location = geocoder.autocomplete(where)
        if location:
            lat, lon = (location.y, location.x)  # update current searched lat/lon
            qs = qs.nearest(location)
        else:
            qs = qs.search_commune(where)
    # pager
    paginator = Paginator(qs, qs.count())
    pager = paginator.get_page(request.GET.get("page", 1))
    geojson_list = make_geojson(pager)
    return render(
        request,
        "search/global_map.html",
        context={
            "commune": commune,
            "paginator": paginator,
            "pager": pager,
            "lat": lat,
            "lon": lon,
            "code": code,
            "what": what,
            "where": where,
            "geojson_list": geojson_list,
            "commune_json": commune.toTemplateJson() if commune else None,
        },
    )


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
        )
        .published()
        .with_votes()
        .filter(commune_ext__slug=commune, slug=erp_slug)
    )
    if activite_slug:
        base_qs = base_qs.filter(activite__slug=activite_slug)
    erp = get_object_or_404(base_qs)
    nearest_erps = (
        Erp.objects.select_related("accessibilite", "activite", "commune_ext")
        .published()
        .nearest(erp.geom)
        .filter(distance__lt=Distance(km=20))[:10]
    )
    geojson_list = make_geojson(nearest_erps)
    form = forms.ViewAccessibiliteForm(instance=erp.accessibilite)
    accessibilite_data = form.get_accessibilite_data()
    user_vote = (
        request.user.is_authenticated
        and not Vote.objects.filter(user=request.user, erp=erp).exists()
        and request.user != erp.user
    )
    user_is_subscribed = request.user.is_authenticated and erp.is_subscribed_by(
        request.user
    )
    url_widget_js = f"{settings.SITE_ROOT_URL}/static/js/widget.js"

    widget_tag = f"""<div id="widget-a11y-container" data-pk="{erp.uuid}" data-baseurl="{settings.SITE_ROOT_URL}"></div>\n
<a href="#" aria-haspopup="dialog" aria-controls="dialog">Accessibilité</a>
<script src="{url_widget_js}" type="text/javascript" async="true"></script>\n"""
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
            "widget_tag": widget_tag,
            "url_widget_js": url_widget_js,
            "root_url": settings.SITE_ROOT_URL,
            "user_is_subscribed": user_is_subscribed,
            "user_vote": user_vote,
        },
    )


def from_uuid(request, uuid):
    erp = get_object_or_404(Erp.objects.published(), uuid=uuid)
    return redirect(erp.get_absolute_url())


def widget_from_uuid(request, uuid):  # noqa
    erp = get_object_or_404(Erp.objects.published(), uuid=uuid)
    accessibilite_data = {}
    access = erp.accessibilite

    # Conditions Stationnement
    stationnement_label = None
    if access.stationnement_presence and erp.accessibilite.stationnement_pmr:
        stationnement_label = "Stationnement adapté dans l'établissement"
    elif access.stationnement_ext_presence and access.stationnement_ext_pmr:
        stationnement_label = "Stationnement adapté à proximité"
    elif access.stationnement_ext_presence and access.stationnement_ext_pmr is False:
        stationnement_label = "Pas de stationnement adapté à proximité"

    if stationnement_label:
        accessibilite_data["stationnement"] = {
            "label": stationnement_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/car.png",
        }

    # Conditions Chemin Extérieur
    chemin_ext_label = None
    if not erp.accessibilite.cheminement_ext_presence:
        pass
    elif (
        erp.accessibilite.cheminement_ext_presence is True
        and erp.accessibilite.cheminement_ext_plain_pied is True
        and (
            erp.accessibilite.cheminement_ext_terrain_stable in (True, None)
        )  # TODO : Accidenté à Modifier
        and (
            erp.accessibilite.cheminement_ext_pente_presence in (False, None)
            or (
                erp.accessibilite.cheminement_ext_pente_degre_difficulte
                == schema.PENTE_LEGERE
            )
        )
        and erp.accessibilite.cheminement_ext_devers
        in (schema.DEVERS_AUCUN, schema.DEVERS_LEGER, None)
        and not erp.accessibilite.cheminement_ext_retrecissement
    ):
        chemin_ext_label = "Chemin d’accès de plain pied"
    elif (
        erp.accessibilite.cheminement_ext_presence is True
        and erp.accessibilite.cheminement_ext_plain_pied is False
        and (
            (
                erp.accessibilite.cheminement_ext_ascenseur
                or erp.accessibilite.cheminement_ext_rampe
            )
        )
        and (erp.accessibilite.cheminement_ext_terrain_stable in (True, None))
        and (
            erp.accessibilite.cheminement_ext_pente_presence in (False, None)
            or (
                erp.accessibilite.cheminement_ext_pente_degre_difficulte
                == schema.PENTE_LEGERE
            )
        )
        and erp.accessibilite.cheminement_ext_devers
        in (schema.DEVERS_AUCUN, schema.DEVERS_LEGER, None)
        and not erp.accessibilite.cheminement_ext_retrecissement
    ):
        chemin_ext_label = "Chemin rendu accessible (%s)" % (
            "rampe" if erp.accessibilite.cheminement_ext_rampe else "ascenseur"
        )
    elif (
        not erp.accessibilite.cheminement_ext_terrain_stable
        or erp.accessibilite.cheminement_ext_pente_degre_difficulte
        == schema.PENTE_IMPORTANTE
        or erp.accessibilite.cheminement_ext_devers == schema.DEVERS_IMPORTANT
        or erp.accessibilite.cheminement_ext_retrecissement
        or (
            not erp.accessibilite.cheminement_ext_ascenseur
            and erp.accessibilite.cheminement_ext_rampe in (schema.RAMPE_AUCUNE, None)
            and erp.accessibilite.cheminement_ext_plain_pied is False
        )
    ):
        chemin_ext_label = "Difficulté sur le chemin d'accès"

    # Conditions Entrée
    entree_label = None
    if erp.accessibilite.entree_plain_pied is True and (
        erp.accessibilite.entree_largeur_mini is None
        or erp.accessibilite.entree_largeur_mini >= 80
    ):
        entree_label = "Entrée de plain pied"
    elif (
        erp.accessibilite.entree_plain_pied is True
        and (
            erp.accessibilite.entree_largeur_mini is not None
            and erp.accessibilite.entree_largeur_mini
        )
        < 80
    ):
        entree_label = "Entrée de plain pied mais étroite"

    elif (
        erp.accessibilite.entree_plain_pied is False
        and not erp.accessibilite.entree_pmr
        and erp.accessibilite.entree_ascenseur
        and (
            erp.accessibilite.entree_largeur_mini is None
            or erp.accessibilite.entree_largeur_mini >= 80
        )
    ):
        entree_label = "Accès à l'entrée par ascenseur"
    elif (
        erp.accessibilite.entree_plain_pied is False
        and not erp.accessibilite.entree_pmr
        and erp.accessibilite.entree_ascenseur
        and (
            erp.accessibilite.entree_largeur_mini is not None
            and erp.accessibilite.entree_largeur_mini < 80
        )
    ):
        entree_label = "Entrée rendue accessible par ascenseur mais étroite"
    elif (
        erp.accessibilite.entree_plain_pied is False
        and not erp.accessibilite.entree_pmr
        and not erp.accessibilite.entree_ascenseur
        and erp.accessibilite.entree_marches_rampe
        in (schema.RAMPE_FIXE, schema.RAMPE_AMOVIBLE)
        and (
            erp.accessibilite.entree_largeur_mini is not None
            and erp.accessibilite.entree_largeur_mini < 80
        )
    ):
        entree_label = "Entrée rendue accessible par rampe mais étroite"
    elif (
        erp.accessibilite.entree_plain_pied is False
        and not erp.accessibilite.entree_pmr
        and not erp.accessibilite.entree_ascenseur
        and erp.accessibilite.entree_marches_rampe
        in (schema.RAMPE_FIXE, schema.RAMPE_AMOVIBLE)
        and (
            erp.accessibilite.entree_largeur_mini is None
            or (
                erp.accessibilite.entree_largeur_mini is not None
                and erp.accessibilite.entree_largeur_mini >= 80
            )
        )
    ):
        entree_label = "Accès à l’entrée par une rampe"
    elif (
        erp.accessibilite.entree_plain_pied is False
        and not erp.accessibilite.entree_pmr
        and not erp.accessibilite.entree_ascenseur
        and erp.accessibilite.entree_marches_rampe in (schema.RAMPE_AUCUNE, None)
    ):
        entree_label = "L’entrée n’est pas de plain-pied"
        if erp.accessibilite.entree_aide_humaine is True:
            entree_label += "\n Aide humaine possible"
    elif (
        erp.accessibilite.entree_plain_pied in (False, None)
        and erp.accessibilite.entree_pmr is True
    ):
        entree_label = "Entrée spécifique PMR"

    if chemin_ext_label and entree_label:
        accessibilite_data["accès"] = {
            "label": f"{chemin_ext_label} \n {entree_label}",
            "icon": f"{settings.SITE_ROOT_URL}/static/img/path.png",
        }
    elif chemin_ext_label:
        accessibilite_data["accès"] = {
            "label": chemin_ext_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/path.png",
        }
    elif entree_label:
        accessibilite_data["accès"] = {
            "label": entree_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/path.png",
        }

    # Conditions présence de personnel
    presence_personnel_label = None
    if erp.accessibilite.accueil_personnels == schema.PERSONNELS_AUCUN:
        presence_personnel_label = "Aucun personnel"
    elif erp.accessibilite.accueil_personnels == schema.PERSONNELS_NON_FORMES:
        presence_personnel_label = "Personnel non formé"
    elif erp.accessibilite.accueil_personnels == schema.PERSONNELS_FORMES:
        presence_personnel_label = "Personnel sensibilisé / formé"

    if presence_personnel_label:
        accessibilite_data["personnel"] = {
            "label": presence_personnel_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/people.png",
        }

    # Conditions présence d'une balise sonore
    balise_sonore = None
    if erp.accessibilite.entree_balise_sonore:
        balise_sonore = "Balise sonore"

    if balise_sonore:
        accessibilite_data["balise sonore"] = {
            "label": balise_sonore,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/people.png",
        }

    # Conditions Présence d’équipement sourd et malentendant
    presence_equipement_sourd_label = None
    if (
        erp.accessibilite.accueil_equipements_malentendants_presence
        and erp.accessibilite.accueil_equipements_malentendants
    ):
        presence_equipement_sourd_label = ", ".join(
            map_list_from_schema(
                schema.EQUIPEMENT_MALENTENDANT_CHOICES,
                erp.accessibilite.accueil_equipements_malentendants,
                verbose=True,
            )
        )

    if presence_equipement_sourd_label:
        accessibilite_data["équipements sourd et malentendant"] = {
            "label": presence_equipement_sourd_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/assistive-listening-systems.png",
        }

    # Conditions Sanitaire
    presence_sanitaire_label = None
    if erp.accessibilite.sanitaires_presence and erp.accessibilite.sanitaires_adaptes:
        presence_sanitaire_label = "Sanitaire adapté"
    elif (
        erp.accessibilite.sanitaires_presence
        and not erp.accessibilite.sanitaires_adaptes
    ):
        presence_sanitaire_label = "Sanitaire non adapté"

    if presence_sanitaire_label:
        accessibilite_data["sanitaire"] = {
            "label": presence_sanitaire_label,
            "icon": f"{settings.SITE_ROOT_URL}/static/img/wc.png",
        }
    return render(
        request,
        "erp/widget.html",
        context={
            "accessibilite_data": accessibilite_data,
            "erp": erp,
            "base_url": f"{settings.SITE_ROOT_URL}",
        },
    )


@login_required
def vote(request, erp_slug):
    if not request.user.is_active:
        raise Http404("Only active users can vote")
    erp = get_object_or_404(
        Erp, slug=erp_slug, published=True, accessibilite__isnull=False
    )
    if request.user == erp.user:
        return HttpResponseBadRequest(
            "Vous ne pouvez pas voter sur votre établissement"
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
@create_revision(request_creates_revision=lambda x: True)
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


def contrib_start(request):
    form = forms.ProviderGlobalSearchForm(request.GET if request.GET else None)
    if form.is_valid():
        return redirect(
            f"{reverse('contrib_global_search')}?{urllib.parse.urlencode(form.cleaned_data)}"
        )
    return render(
        request,
        template_name="contrib/0-start.html",
        context={
            "form": form,
        },
    )


def contrib_global_search(request):
    results = error = None
    what_lower = request.GET.get("what").lower()
    try:
        results = provider_search.global_search(what_lower, request.GET.get("code"))
        qs_results_bdd = Erp.objects.select_related(
            "accessibilite", "activite", "commune_ext"
        ).search_what(what_lower)

        commune, qs_results_bdd = _search_commune_code_postal(
            qs_results_bdd, request.GET.get("code")
        )

        results_bdd, results = acceslibre.parse_etablissements(qs_results_bdd, results)
    except RuntimeError as err:
        error = err
    return render(
        request,
        template_name="contrib/0a-search_results.html",
        context={
            "what": request.GET.get("what"),
            "commune_search": commune,
            "step": 1,
            "libelle_step": {
                "current": "informations",
                "next": schema.SECTION_TRANSPORT,
            },
            "results_bdd": results_bdd,
            "results": results,
            "error": error,
            "results_global_count": len(results) + len(results_bdd),
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_admin_infos(request):
    data = erp = external_erp = None
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
                if request.user.is_authenticated and erp.user is None:
                    erp.user = request.user
                erp.save()
                if erp.activite.nom == "Autre":
                    Activite.notify_admin(
                        new_activity=form.cleaned_data["nouvelle_activite"], erp=erp
                    )
                messages.add_message(
                    request, messages.SUCCESS, "Les données ont été enregistrées."
                )
                return redirect("contrib_a_propos", erp_slug=erp.slug)
    else:
        encoded_data = request.GET.get("data")
        try:
            data = serializers.decode_provider_data(encoded_data)
        except RuntimeError as err:
            data_error = err
        else:
            data_erp = data.copy()
            if "coordonnees" in data_erp:
                del data_erp["coordonnees"]
            if "naf" in data_erp:
                del data_erp["naf"]
            if "lat" in data_erp:
                del data_erp["lat"]
            if "lon" in data_erp:
                del data_erp["lon"]
            external_erp = Erp(**data_erp)
        form = forms.PublicErpAdminInfosForm(initial=data)

    geojson_list = make_geojson(existing_matches) if existing_matches else None

    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "libelle_step": {
                "current": "informations",
                "next": schema.SECTION_A_PROPOS,
            },
            "form": form,
            "has_data": data is not None,
            "data_error": data_error,
            "existing_matches": existing_matches,
            "geojson_list": geojson_list,
            "erp": erp,
            "external_erp": external_erp,
            "activite": Activite.objects.get(nom="Autre"),
        },
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_edit_infos(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)
    initial = {"lat": float(erp.geom.y), "lon": float(erp.geom.x)}
    if request.user.is_authenticated and erp.user is request.user:
        libelle_next = schema.SECTION_A_PROPOS
        next_route = schema.SECTIONS[schema.SECTION_A_PROPOS]["edit_route"]
    else:
        libelle_next = schema.SECTION_TRANSPORT
        next_route = schema.SECTIONS[schema.SECTION_TRANSPORT]["edit_route"]
    if request.method == "POST":
        form = forms.PublicErpEditInfosForm(request.POST, instance=erp)
        if form.is_valid():
            erp = form.save()
            if request.user.is_authenticated and erp.user is None:
                erp.user = request.user
                erp.save()
            if erp.activite.nom == "Autre":
                Activite.notify_admin(
                    new_activity=form.cleaned_data["nouvelle_activite"], erp=erp
                )
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
            )
            return redirect(next_route, erp_slug=erp.slug)
    else:
        form = forms.PublicErpAdminInfosForm(instance=erp, initial=initial)

    return render(
        request,
        template_name="contrib/1-admin-infos.html",
        context={
            "step": 1,
            "libelle_step": {
                "current": "informations",
                "next": libelle_next,
            },
            "erp": erp,
            "form": form,
            "has_data": False,
            "activite": Activite.objects.get(nom="Autre"),
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
        form = forms.PublicAProposForm(
            request.POST, instance=accessibilite, initial=initial
        )
        if form.is_valid():
            erp.user_type = form.data["user_type"]
            accessibilite = form.save(commit=False)
            accessibilite.erp = erp
            accessibilite.save()

            if request.user.is_authenticated and erp.user is None:
                erp.user = request.user
                if form.cleaned_data["subscribe"] is True:
                    ErpSubscription.subscribe(erp, request.user)

            erp.save()
            messages.add_message(
                request, messages.SUCCESS, "Les données ont été enregistrées."
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
            "libelle_step": {
                "current": "informations",
                "next": schema.SECTION_TRANSPORT,
            },
            "erp": erp,
            "form": form,
            "has_data": False,
        },
    )


def check_authentication(request, erp, form, check_online=True):
    redirect_path = redirect(
        reverse("login")
        + "?"
        + urllib.parse.urlencode(
            {"next": request.path + "?" + urllib.parse.urlencode(form.data)}
        )
    )
    if check_online:
        if erp.is_online() and not request.user.is_authenticated:
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
    redirect_hash=None,
    libelle_step=None,
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
    user_can_access_next_route = (
        request.user == erp.user or step not in (8, 9) or not erp.is_online()
    )

    Form = modelform_factory(
        Accessibilite, form=forms.ContribAccessibiliteForm, fields=form_fields
    )

    if request.method == "POST":
        form = Form(request.POST, instance=accessibilite)
    else:
        if request.GET:
            form = Form(request.GET, instance=accessibilite)
        else:
            form = forms.ContribAccessibiliteForm(
                instance=accessibilite, initial={"entree_porte_presence": True}
            )
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
        messages.add_message(
            request, messages.SUCCESS, "Les données ont été enregistrées."
        )
        if "publier" in request.POST:
            return redirect(
                reverse("contrib_publication", kwargs={"erp_slug": erp.slug})
            )

        if user_can_access_next_route:
            return redirect(
                reverse(redirect_route, kwargs={"erp_slug": erp.slug}) + "#content"
            )
        else:
            if erp.is_online():
                redirect_url = erp.get_success_url()
            elif erp.user == request.user:
                redirect_url = reverse("mes_erps")
            else:
                redirect_url = reverse("mes_contributions")
            if step == 8:
                redirect_url += f"#{redirect_hash}"
            return redirect(redirect_url)

    if prev_route:
        prev_route = reverse(prev_route, kwargs={"erp_slug": erp.slug})
    else:
        prev_route = None

    if user_can_access_next_route:
        publier_route = reverse("contrib_publication", kwargs={"erp_slug": erp.slug})
    else:
        publier_route = None

    return render(
        request,
        template_name=template_name,
        context={
            "step": step,
            "libelle_step": libelle_step,
            "erp": erp,
            "form": form,
            "accessibilite": accessibilite,
            "redirect_hash": redirect_hash,
            "publier_route": publier_route,
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
        redirect_hash=schema.SECTION_TRANSPORT,
        libelle_step={
            "current": schema.SECTION_TRANSPORT,
            "next": schema.SECTION_CHEMINEMENT_EXT,
        },
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
        redirect_hash=schema.SECTION_CHEMINEMENT_EXT,
        libelle_step={
            "current": schema.SECTION_CHEMINEMENT_EXT,
            "next": schema.SECTION_ENTREE,
        },
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
        redirect_hash=schema.SECTION_ENTREE,
        libelle_step={"current": schema.SECTION_ENTREE, "next": schema.SECTION_ACCUEIL},
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
        redirect_hash=schema.SECTION_ACCUEIL,
        libelle_step={
            "current": schema.SECTION_ACCUEIL,
            "next": schema.SECTION_COMMENTAIRE,
        },
    )


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
        redirect_hash=schema.SECTION_COMMENTAIRE,
        libelle_step={"current": schema.SECTION_COMMENTAIRE, "next": None},
    )


@create_revision(request_creates_revision=lambda x: True)
def contrib_publication(request, erp_slug):
    erp = get_object_or_404(Erp, slug=erp_slug)

    if request.method == "POST":
        form = forms.PublicPublicationForm(request.POST, instance=erp)
    else:
        if request.GET:
            form = forms.PublicPublicationForm(request.GET, instance=erp)
        else:
            form = forms.PublicPublicationForm({"published": True}, instance=erp)

    if form.is_valid():
        if check_authentication(request, erp, form, check_online=False):
            return check_authentication(request, erp, form, check_online=False)
        erp = form.save()
        if erp.user is None:
            erp.user = request.user
            erp.save()
        ErpSubscription.subscribe(erp, erp.user)
        messages.add_message(
            request, messages.SUCCESS, "Les données ont été sauvegardées."
        )
        if erp.is_online():
            redirect_url = erp.get_success_url()
        elif erp.user == request.user:
            redirect_url = reverse("mes_erps")

        return redirect(redirect_url)

    return render(
        request,
        template_name="contrib/8-publication.html",
        context={
            "step": 8,
            "libelle_step": {"current": "publication", "next": None},
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
