from collections import namedtuple

from django.utils.translation import gettext as translate

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


def global_search(terms, code_insee):
    # OpenDataSoft
    result_ods = opendatasoft.search(terms, code_insee)
    for result in result_ods:
        result["exists"] = Erp.objects.find_similar(
            result["nom"],
            result["commune"],
            voie=result["voie"],
            lieu_dit=result["lieu_dit"],
        ).first()

    # Etalab entreprise
    search_entreprises = f"{terms} {get_searched_commune(code_insee, terms)}"
    result_entreprises = entreprise.search(search_entreprises, code_insee)
    for result in result_entreprises:
        # TODO: Search by short distance around location
        result["exists"] = Erp.objects.find_similar(
            result["nom"],
            result["commune"],
            voie=result["voie"],
            lieu_dit=result["lieu_dit"],
        ).first()

    # Administration publique
    result_public = public_erp.search(terms, code_insee)
    for result in result_public:
        result["exists"] = Erp.objects.find_by_source_id(result["source"], result["source_id"], published=True).first()

    return sort_and_filter_results(code_insee, result_public + result_ods + result_entreprises)


def get_equipments(as_dict: bool = False):
    Equipment = namedtuple("Equipment", ["name", "slug", "manager"])
    equipments = [
        Equipment(
            slug="having_parking", manager=ErpQuerySet.having_parking, name=translate("Stationnement à proximité")
        ),
        Equipment(
            slug="having_public_transportation",
            manager=ErpQuerySet.having_public_transportation,
            name=translate("Transport en commun à proximité"),
        ),
        Equipment(
            slug="having_adapted_parking",
            manager=ErpQuerySet.having_adapted_parking,
            name=translate("Stationnement PMR (dans l'établissement ou à proximité)"),
        ),
        Equipment(
            slug="having_no_path",
            manager=ErpQuerySet.having_no_path,
            name=translate("Pas de chemin extérieur ou donnée inconnue"),
        ),
        Equipment(
            slug="having_proper_surface",
            manager=ErpQuerySet.having_proper_surface,
            name=translate("Extérieur - revêtement stable ou donnée inconnue"),
        ),
        Equipment(
            slug="having_path_low_stairs",
            manager=ErpQuerySet.having_path_low_stairs,
            name=translate("Extérieur - plain pied ou accessible via rampe ou ascenseur"),
        ),
        Equipment(
            slug="having_no_slope",
            manager=ErpQuerySet.having_no_slope,
            name=translate("Extérieur - pas de pente importante ou donnée inconnue"),
        ),
        Equipment(
            slug="having_no_camber",
            manager=ErpQuerySet.having_no_camber,
            name=translate("Extérieur - pas de dévers important ou donnée inconnue"),
        ),
        Equipment(
            slug="having_no_shrink",
            manager=ErpQuerySet.having_no_shrink,
            name=translate("Extérieur - aucun rétrécissement ou donnée inconnue"),
        ),
        Equipment(
            slug="having_nb_stairs_max", manager=ErpQuerySet.having_nb_stairs_max, name=translate("Maximum 1 marche")
        ),  # TODO make the same for entry/reception/ext
        Equipment(
            slug="having_guide_band",
            manager=ErpQuerySet.having_guide_band,
            name=translate("Extérieur - bande de guidage"),
        ),
        Equipment(
            slug="having_accessible_entry",
            manager=ErpQuerySet.having_accessible_entry,
            name=translate("Entrée de plain pied ou accessible via rampe ou ascenseur"),
        ),
        Equipment(
            slug="having_entry_min_width",
            manager=ErpQuerySet.having_entry_min_width,
            name=translate("Largeur de porte supérieure à 80cm ou donnée inconnue"),
        ),
        Equipment(
            slug="having_adapted_entry",
            manager=ErpQuerySet.having_adapted_entry,
            name=translate("Entrée spécifique PMR"),
        ),
        Equipment(
            slug="having_entry_easily_identifiable",
            manager=ErpQuerySet.having_entry_easily_identifiable,
            name=translate("Entrée facilement repérable"),
        ),
        Equipment(slug="having_sound_beacon", manager=ErpQuerySet.having_sound_beacon, name=translate("Balise sonore")),
        Equipment(
            slug="having_visible_reception",
            manager=ErpQuerySet.having_visible_reception,
            name=translate("Visibilité de l'accueil depuis l'entrée"),
        ),
        Equipment(slug="having_staff", manager=ErpQuerySet.having_staff, name=translate("Présence de personnel")),
        Equipment(
            slug="having_trained_staff",
            manager=ErpQuerySet.having_trained_staff,
            name=translate("Personnel sensibilisé ou formé"),
        ),
        Equipment(
            slug="having_audiodescription",
            manager=ErpQuerySet.having_audiodescription,
            name=translate("Audiodescription"),
        ),
        Equipment(
            slug="having_hearing_equipments",
            manager=ErpQuerySet.having_hearing_equipments,
            name=translate("Equipements spécifiques pour personne malentendante"),
        ),
        Equipment(
            slug="having_potentially_all_at_ground_level",
            manager=ErpQuerySet.having_potentially_all_at_ground_level,
            name=translate(
                "Chemin de plain pied jusqu'à l'accueil ou accessible via rampe ou ascenseur ou donnée inconnue"
            ),
        ),
        Equipment(
            slug="having_entry_no_shrink",
            manager=ErpQuerySet.having_entry_no_shrink,
            name=translate("Chemin sans rétrécissement jusqu'à l'accueil ou donnée inconnue"),
        ),
        Equipment(
            slug="having_accessible_rooms",
            manager=ErpQuerySet.having_accessible_rooms,
            name=translate("Chambre accessible"),
        ),
        Equipment(slug="having_adapted_wc", manager=ErpQuerySet.having_adapted_wc, name=translate("Toilette PMR")),
        Equipment(slug="having_label", manager=ErpQuerySet.having_label, name=translate("Label")),
    ]

    if as_dict:
        return {eq.slug: eq.name for eq in equipments}
    return equipments


def get_equipment_by_slug(slug: str):
    if not slug:
        return None
    equipments = get_equipments()
    for equipment in equipments:
        if equipment.slug == slug:
            return equipment

    return None


def filter_erps_by_equipments(queryset, equipments: list):
    if not equipments:
        return queryset

    for eq_slug in equipments:
        equipment = get_equipment_by_slug(eq_slug)
        if not equipment:
            continue

        queryset = getattr(queryset, equipment.manager.__name__)()

    return queryset
