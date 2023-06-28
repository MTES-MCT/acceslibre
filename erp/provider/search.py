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


def equipments_filters():
    # Equipment = namedtuple("Equipment", ["name", "slug", "manager"])
    return {
        "having_parking": "Stationnement à proximité",
        "having_public_transportation": "Transport en commun à proximité",
        "having_adapted_parking": "Stationnement PMR (dans l'établissement ou à proximité)",
        "having_no_path": "Pas de chemin extérieur ou donnée inconnue",
        "having_proper_surface": "Extérieur - revêtement stable ou donnée inconnue",
        "having_path_low_stairs": "Extérieur - plain pied ou accessible via rampe ou ascenseur",
        "having_no_slope": "Extérieur - pas de pente importante ou donnée inconnue",
        "having_no_camber": "Extérieur - pas de dévers important ou donnée inconnue",
        "having_no_shrink": "Extérieur - aucun rétrécissement ou donnée inconnue",
        "having_nb_stairs_max": "Maximum 1 marche",  # TODO make the same for entry/reception/ext
        "having_guide_band": "Extérieur - bande de guidage",
        "having_accessible_entry": "Entrée de plain pied ou accessible via rampe ou ascenseur",
        "having_entry_min_width": "Largeur de porte supérieure à 80cm ou donnée inconnue",
        "having_adapted_entry": "Entrée spécifique PMR",
        "having_entry_easily_identifiable": "Entrée facilement repérable",
        "having_sound_beacon": "Balise sonore",
        "having_visible_reception": "Visibilité de l'accueil depuis l'entrée",
        "having_staff": "Présence de personnel",
        "having_trained_staff": "Personnel sensibilisé ou formé",
        "having_audiodescription": "Audiodescription",
        "having_hearing_equipments": "Equipements spécifiques pour personne malentendante",
        # "Chemin de plain pied jusqu'à l'accueil ou accessible via rampe ou ascenseur ou donnée inconnue",
        "having_entry_no_shrink": "Chemin sans rétrécissement jusqu'à l'accueil ou donnée inconnue",
        "having_accessible_rooms": "Chambre accessible",
        "having_adapted_wc": "Toilette PMR",
        "having_label": "Label",
    }


# from erp.models import *
# from erp.provider.search import equipments_filters

# qs = Erp.objects.all()
# for eq in equipments_filters():
#     nb = getattr(qs, eq)().count()
#     print(f"NB ERP returned using filter `{eq}`: {nb}")
