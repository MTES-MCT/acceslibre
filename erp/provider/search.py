from collections import namedtuple
from dataclasses import dataclass

from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext as translate

from core.lib import geo
from erp.managers import ErpQuerySet
from erp.models import Commune, Erp
from erp.provider import arrondissements, entreprise, opendatasoft, public_erp


def get_searched_commune(code_insee, search):
    commune = Commune.objects.filter(code_insee=code_insee).first()
    if commune:
        return commune.nom
    # lookup arrondissements
    arrdt = arrondissements.get_by_code_insee(code_insee)
    return arrdt["commune"] if arrdt else ""


def sort_and_filter_results(code_insee, results):
    siret_seen = []
    processed = []

    for result in results:
        # Exclude non-geolocalized results
        if result.get("coordonnees") is None:
            continue
        # Exclude results from other departements
        if result["code_insee"][:2] != code_insee[:2]:
            continue
        # Exclude already seen siret
        siret = result.get("siret")
        if siret:
            if siret in siret_seen:
                continue
            else:
                siret_seen.append(result.get("siret"))
        processed.append(result)

    # Sort with matching commune first (same insee code)
    processed = sorted(
        processed,
        key=lambda result: result["code_insee"] == code_insee,
        reverse=True,
    )

    return processed


def global_search(terms, code_insee, activity):
    def _populate_with_activity(entry):
        if not activity:
            return entry

        entry["activite"] = activity.pk
        entry["activite_slug"] = activity.slug
        return entry

    # OpenDataSoft sirene V3
    naf_ape_codes = ",".join(activity.naf_ape_code) if activity else None
    result_ods = opendatasoft.search(terms, code_insee)
    for result in result_ods:
        result["exists"] = Erp.objects.find_similar(
            result["nom"],
            result["commune"],
            voie=result["voie"],
            lieu_dit=result["lieu_dit"],
        ).first()
        result = _populate_with_activity(result)

    # API entreprise
    search_entreprises = f"{terms} {get_searched_commune(code_insee, terms)}"
    result_entreprises = entreprise.search(search_entreprises, code_insee, naf_ape_codes)
    for result in result_entreprises:
        # TODO: Search by short distance around location
        result["exists"] = Erp.objects.find_similar(
            result["nom"],
            result["commune"],
            voie=result["voie"],
            lieu_dit=result["lieu_dit"],
        ).first()
        result = _populate_with_activity(result)

    # Administration publique
    result_public = public_erp.search(terms, code_insee)
    for result in result_public:
        result["exists"] = Erp.objects.find_by_source_id(result["source"], result["source_id"], published=True).first()
        result = _populate_with_activity(result)

    return sort_and_filter_results(code_insee, result_public + result_ods + result_entreprises)


def get_equipments():
    ACCESS_GROUP = translate("Accès")
    SERVICES_GROUP = translate("Accueil et prestations")
    OUTSIDE_GROUP = translate("Extérieur")
    ENTRANCE_GROUP = translate("Entrée")
    Equipment = namedtuple(
        "Equipment",
        ["name", "slug", "manager", "is_default_suggestion", "group"],
        defaults=(None, None, None, False, "default"),
    )
    equipments = [
        Equipment(
            slug="having_parking",
            manager=ErpQuerySet.having_parking,
            name=translate("Stationnement à proximité"),
            group=ACCESS_GROUP,
        ),
        Equipment(
            slug="having_public_transportation",
            manager=ErpQuerySet.having_public_transportation,
            name=translate("Transport en commun à proximité"),
            group=ACCESS_GROUP,
        ),
        Equipment(
            slug="having_adapted_parking",
            manager=ErpQuerySet.having_adapted_parking,
            name=translate("Stationnement PMR (dans l'établissement ou à proximité)"),
            group=ACCESS_GROUP,
        ),
        Equipment(
            slug="having_no_path",
            manager=ErpQuerySet.having_no_path,
            name=translate("Pas de chemin extérieur ou information inconnue"),
            group=OUTSIDE_GROUP,
        ),
        Equipment(
            slug="having_adapted_path",
            manager=ErpQuerySet.having_adapted_path,
            name=translate("Chemin adapté aux personnes mal marchantes"),
            group=OUTSIDE_GROUP,
        ),
        Equipment(
            slug="having_path_low_stairs",
            manager=ErpQuerySet.having_path_low_stairs,
            name=translate("Extérieur - plain-pied ou accessible via rampe ou ascenseur"),
            group=OUTSIDE_GROUP,
        ),
        Equipment(
            slug="having_entry_low_stairs",
            manager=ErpQuerySet.having_entry_low_stairs,
            name=translate("Maximum une marche à l'entrée"),
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_reception_low_stairs",
            manager=ErpQuerySet.having_reception_low_stairs,
            name=translate("Maximum une marche à l'accueil"),
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_accessible_exterior_path",
            manager=ErpQuerySet.having_accessible_exterior_path,
            name=translate("Chemin extérieur accessible"),
            group=OUTSIDE_GROUP,
        ),
        Equipment(
            slug="having_guide_band",
            manager=ErpQuerySet.having_guide_band,
            name=translate("Extérieur - bande de guidage"),
            group=OUTSIDE_GROUP,
        ),
        Equipment(
            slug="having_accessible_entry",
            manager=ErpQuerySet.having_accessible_entry,
            name=translate("Entrée accessible"),
            is_default_suggestion=True,
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_accessible_path_to_reception",
            manager=ErpQuerySet.having_accessible_path_to_reception,
            name=translate("Chemin vers l'accueil accessible"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_entry_min_width",
            manager=ErpQuerySet.having_entry_min_width,
            name=translate("Largeur de porte supérieure à 80cm ou information inconnue"),
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_adapted_entry",
            manager=ErpQuerySet.having_adapted_entry,
            name=translate("Entrée spécifique PMR"),
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_sound_beacon",
            manager=ErpQuerySet.having_sound_beacon,
            name=translate("Balise sonore"),
            group=ENTRANCE_GROUP,
        ),
        Equipment(
            slug="having_entry_call_device",
            manager=ErpQuerySet.having_entry_call_device,
            name=translate("Dispositif d'appel à l'entrée"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_visible_reception",
            manager=ErpQuerySet.having_visible_reception,
            name=translate("Proximité de l'accueil"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_staff",
            manager=ErpQuerySet.having_staff,
            name=translate("Présence de personnel"),
            is_default_suggestion=True,
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_trained_staff",
            manager=ErpQuerySet.having_trained_staff,
            name=translate("Personnel sensibilisé ou formé"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_audiodescription",
            manager=ErpQuerySet.having_audiodescription,
            name=translate("Audiodescription"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_hearing_equipments",
            manager=ErpQuerySet.having_hearing_equipments,
            name=translate("Equipements spécifiques pour personne malentendante"),
            is_default_suggestion=True,
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_entry_no_shrink",
            manager=ErpQuerySet.having_entry_no_shrink,
            name=translate("Chemin sans rétrécissement jusqu'à l'accueil ou information inconnue"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_accessible_rooms",
            manager=ErpQuerySet.having_accessible_rooms,
            name=translate("Chambre accessible"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_adapted_wc",
            manager=ErpQuerySet.having_adapted_wc,
            name=translate("Toilettes PMR"),
            group=SERVICES_GROUP,
        ),
        Equipment(
            slug="having_label",
            manager=ErpQuerySet.having_label,
            name=translate("Établissement labellisé"),
            group=SERVICES_GROUP,
        ),
    ]

    return {eq.slug: eq for eq in equipments}


def filter_erps_by_equipments(queryset, equipments: list):
    if not equipments:
        return queryset

    all_equipments = get_equipments()

    for eq_slug in equipments:
        equipment = all_equipments.get(eq_slug)
        if not equipment:
            continue

        queryset = getattr(queryset, equipment.manager.__name__)()

    return queryset


@dataclass
class EquipmentsShortcut:
    name: str
    slug: str
    equipments: list
    suggestions: list
    icon: str

    @property
    def equipments_as_list(self):
        return ",".join([e.slug for e in self.equipments])

    @property
    def suggestions_as_list(self):
        return ",".join([e.slug for e in self.suggestions])


def get_equipments_shortcuts():
    all_equipments = get_equipments()
    difficulty_of_vision = EquipmentsShortcut(
        name=translate("Difficulté à voir"),
        slug="difficulty_of_vision",
        equipments=[],
        suggestions=[
            all_equipments.get("having_staff"),
            all_equipments.get("having_visible_reception"),
            all_equipments.get("having_audiodescription"),
            all_equipments.get("having_guide_band"),
            all_equipments.get("having_sound_beacon"),
            all_equipments.get("having_public_transportation"),
            all_equipments.get("having_parking"),
        ],
        icon="diff-vision",
    )
    wheeling_chair = EquipmentsShortcut(
        name=translate("En fauteuil roulant"),
        slug="wheeling_chair",
        equipments=[
            all_equipments.get("having_accessible_exterior_path"),
            all_equipments.get("having_accessible_entry"),
            all_equipments.get("having_accessible_path_to_reception"),
        ],
        suggestions=[
            all_equipments.get("having_public_transportation"),
            all_equipments.get("having_adapted_parking"),
            all_equipments.get("having_adapted_wc"),
            all_equipments.get("having_accessible_rooms"),
        ],
        icon="wheelchair",
    )
    difficulty_walking = EquipmentsShortcut(
        name=translate("Difficulté à marcher"),
        slug="difficulty_walking",
        equipments=[
            all_equipments.get("having_adapted_path"),
            all_equipments.get("having_entry_low_stairs"),
            all_equipments.get("having_reception_low_stairs"),
        ],
        suggestions=[
            all_equipments.get("having_staff"),
            all_equipments.get("having_adapted_wc"),
        ],
        icon="diff-walking",
    )
    deaf_person = EquipmentsShortcut(
        name=translate("Difficulté à entendre"),
        slug="deaf",
        equipments=[all_equipments.get("having_trained_staff")],
        suggestions=[all_equipments.get("having_hearing_equipments")],
        icon="deaf",
    )
    hard_to_understand = EquipmentsShortcut(
        name=translate("Difficulté à comprendre"),
        slug="hard_to_understand",
        equipments=[all_equipments.get("having_trained_staff")],
        suggestions=[],
        icon="diff-understand",
    )
    return [difficulty_of_vision, wheeling_chair, difficulty_walking, deaf_person, hard_to_understand]


def _parse_location_or_404(lat, lon):
    if not lat or not lon:
        return None
    try:
        return geo.parse_location((lat, lon))
    except RuntimeError as err:
        raise Http404(err)


def filter_erp_by_location(queryset, **kwargs):
    search_type = kwargs.get("search_type")
    lat, lon = kwargs.get("lat"), kwargs.get("lon")
    location = _parse_location_or_404(lat, lon)
    postcode = kwargs.get("postcode")

    if search_type == settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_CITY:
        return queryset.filter(
            commune__iexact=kwargs.get("city"), code_postal__startswith=kwargs.get("code_departement")
        )
    if search_type == settings.IN_DEPARTMENT_SEARCH_TYPE:
        code = "20" if kwargs.get("code").lower() in ["2a", "2b"] else kwargs.get("code")
        return queryset.filter(code_postal__startswith=code)
    if search_type in (settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_HOUSENUMBER, "Autour de moi", translate("Autour de moi")):
        return queryset.nearest(location, max_radius_km=0.2)

    if search_type == settings.ADRESSE_DATA_GOUV_SEARCH_TYPE_STREET:
        street_name = kwargs.get("street_name")
        return queryset.filter(code_postal=postcode, voie__icontains=street_name)
    return queryset
