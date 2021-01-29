import logging
import requests

from fuzzywuzzy import process as fuzzy_process

from core.lib import text
from erp.models import Activite, Commune

logger = logging.getLogger(__name__)

MAX_TYPES = 5
MIN_SCORE = 70

BASE_URL = "https://etablissements-publics.api.gouv.fr/v3"

TYPES = {
    "mairie": {
        "description": "Mairie",
        "searches": ["hotel de ville"],
    },
    "commissariat_police": {
        "description": "Commissariat de police",
    },
    "maison_arret": {
        "description": "Maison d'arrêt",
        "searches": ["prison", "penitencier", "prison", "detention"],
    },
    "maison_handicapees": {
        "description": "Maison départementale des personnes handicapées (MDPH)",
    },
    "pmi": {
        "description": "Centre de protection maternelle et infantile (PMI)",
    },
    "pole_emploi": {
        "description": "Pôle emploi",
        "searches": ["anpe", "assedic"],
    },
    "prefecture": {
        "description": "Préfecture",
        "searches": ["prefecture de police"],
    },
    "sous_pref": {
        "description": "Sous-préfecture",
    },
    "accompagnement_personnes_agees": {
        "description": "Plateforme d'accompagnement et de répit pour les aidants de personnes âgées",
        "searches": ["gériatrie"],
    },
    "adil": {
        "description": "Information sur le logement (Agence départementale pour l'information sur le logement, ADIL) départementale",
    },
    "afpa": {
        "description": "Association nationale pour la formation professionnelle des adultes (AFPA), réseau local",
    },
    "anah": {
        "description": "Agence nationale de l'habitat (ANAH), réseau local",
    },
    "apec": {
        "description": "Association pour l'emploi des cadres (APEC)",
        "searches": ["pole emploi"],
    },
    "apecita": {
        "description": "Association pour l'emploi des cadres, ingénieurs et techniciens de l'agriculture et de l'agroalimentaire (APECITA), réseau local",
    },
    "ars_antenne": {
        "description": "Délégation territoriale de l'Agence régionale de santé",
        "searches": ["ars"],
    },
    "banque_de_france": {
        "description": "Banque de France, succursale",
    },
    "bav": {
        "description": "Bureau d'aide aux victimes",
    },
    "bsn": {
        "description": "Bureau ou centre du service national",
        "searches": ["snu", "civique"],
    },
    "caa": {
        "description": "Cour administrative d'appel",
    },
    "caf": {
        "description": "Caisse d'allocations familiales (CAF)",
    },
    "carsat": {
        "description": "Caisse d'assurance retraite et de la santé au travail (CARSAT)",
    },
    "ccas": {
        "description": "Centre communal d'action sociale",
    },
    "cci": {
        "description": "Chambre de commerce et d'industrie (CCI)",
    },
    "cdas": {
        "description": "Centre départemental d'action sociale",
    },
    "cdg": {
        "description": "Centre de gestion de la fonction publique territoriale",
        "searches": ["cgfpt"],
    },
    "centre_detention": {
        "description": "Centre de détention",
        "searches": ["prison", "maison d'arret", "penitencier", "detention"],
    },
    "centre_impots_fonciers": {
        "description": "Centre des impôts foncier et cadastre",
        "searches": ["impots"],
    },
    "centre_penitentiaire": {
        "description": "Centre pénitentiaire",
        "searches": ["prison", "maison d'arret", "detention"],
    },
    "centre_social": {
        "description": "Centre social",
    },
    "cg": {
        "description": "Conseil départemental",
    },
    "chambre_agriculture": {
        "description": "Chambre d'agriculture",
    },
    "chambre_metier": {
        "description": "Chambre de métiers et de l'artisanat",
        "searches": ["cma"],
    },
    "cicas": {
        "description": "Centre d'information de conseil et d'accueil des salariés (CICAS)",
    },
    "cidf": {
        "description": "Centre d'information sur les droits des femmes et des familles (CIDFF)",
    },
    "cij": {
        "description": "Information jeunesse, réseau local",
    },
    "cio": {
        "description": "Centre d'information et d'orientation (CIO)",
    },
    "civi": {
        "description": "Commission d'indemnisation des victimes d'infraction",
    },
    "clic": {
        "description": "Point d'information local dédié aux personnes âgées",
    },
    "cnfpt": {
        "description": "Centre national de la fonction publique territoriale (CNFPT), réseau local",
    },
    "commission_conciliation": {
        "description": "Commission départementale de conciliation",
    },
    "conciliateur_fiscal": {
        "description": "Conciliateur fiscal",
    },
    "cour_appel": {
        "description": "Cour d'appel",
    },
    "cpam": {
        "description": "Caisse primaire d'assurance maladie (CPAM)",
    },
    "cr": {
        "description": "Conseil régional",
    },
    "crib": {
        "description": "Centre de ressources et d'information des bénévoles (CRIB)",
    },
    "crous": {
        "description": "CROUS et ses antennes",
    },
    "csl": {
        "description": "Centre de semi-liberté",
    },
    "ddcs": {
        "description": "Direction départementale de la cohésion sociale (DDCS)",
    },
    "ddcspp": {
        "description": "Direction départementale de la cohésion sociale et de la protection des populations (DDCSPP)",
    },
    "ddpp": {
        "description": "Protection des populations (direction départementale, DDPP)",
    },
    "ddt": {
        "description": "Direction départementale des territoires -et de la mer- (DDT)",
    },
    "direccte_ut": {
        "description": "Unité territoriale - Direction régionale des entreprises, de la concurrence, de la consommation, du travail et de l'emploi",
        "searches": ["direccte"],
    },
    "dml": {
        "description": "Délégation à la mer et au littoral",
    },
    "drac": {
        "description": "Direction régionale des affaires culturelles (DRAC)",
    },
    "draf": {
        "description": "Direction régionale de l'alimentation, de l'agriculture et de la forêt (DRAAF)",
    },
    "drddi": {
        "description": "Direction interrégionale et régionale des douanes",
    },
    "dreal": {
        "description": "Direction régionale de l'environnement, de l'aménagement et du logement (DREAL)",
    },
    "dreal_ut": {
        "description": "Unité territoriale - Direction régionale de l'environnement, de l'aménagement et du logement (DREAL)",
    },
    "driea_ut": {
        "description": "Unité territoriale - Direction régionale et interdépartementale de l'équipement et de l'aménagement (DRIEA)",
    },
    "edas": {
        "description": "Établissement départemental d'actions sociales (EDAS)",
    },
    "epci": {
        "description": "Intercommunalité",
        "searches": ["agglomération"],
    },
    "esm": {
        "description": "Etablissement spécialisé pour mineurs",
    },
    "fdapp": {
        "description": "Fédération départementale pour la pêche et la protection du milieu aquatique (FDPPMA)",
    },
    "fdc": {
        "description": "Fédération départementale des chasseurs",
    },
    "gendarmerie": {
        "description": "Brigade de gendarmerie",
    },
    "greta": {
        "description": "Greta",
    },
    "hypotheque": {
        "description": "Service de publicité foncière ex-conservation des hypothèques",
    },
    "inspection_academique": {
        "description": "Direction des services départementaux de l'Éducation nationale (DSDEN)",
    },
    "maia": {
        "description": "Mission d'accueil et d'information des associations (MAIA)",
    },
    "mairie_com": {
        "description": "Mairie des collectivités d'outre-mer",
    },
    "mairie_mobile": {
        "description": "Mairie mobile de la ville de Paris",
    },
    "maison_centrale": {
        "description": "Maison centrale",
    },
    "mds": {
        "description": "Maison départementale des solidarités",
    },
    "mission_locale": {
        "description": "Mission locale et Permanence d'accueil, d'information et d'orientation (PAIO)",
    },
    "mjd": {
        "description": "Maison de justice et du droit",
    },
    "msa": {
        "description": "Mutualité sociale agricole (MSA), réseau local",
    },
    "ofii": {
        "description": "Office français de l'immigration et de l'intégration (ex ANAEM), réseau local",
    },
    "onac": {
        "description": "Office national des anciens combattants (ONAC), réseau local",
    },
    "paris_mairie": {
        "description": "Mairie de Paris, Hôtel de Ville",
    },
    "paris_ppp": {
        "description": "Préfecture de police de Paris",
    },
    "paris_ppp_antenne": {
        "description": "Préfecture de police de Paris, antenne d'arrondissement",
    },
    "paris_ppp_certificat_immatriculation": {
        "description": "Préfecture de police de Paris, certificat d'immatriculation",
    },
    "paris_ppp_gesvres": {
        "description": "Préfecture de police de Paris - Site central de Gesvres",
    },
    "paris_ppp_permis_conduire": {
        "description": "Préfecture de police de Paris, permis de conduire",
    },
    "permanence_juridique": {
        "description": "Permanence juridique",
    },
    "pif": {
        "description": "Point info famille",
    },
    "prefecture_greffe_associations": {
        "description": "Greffe des associations",
    },
    "prefecture_region": {
        "description": "Préfecture de région",
    },
    "prudhommes": {
        "description": "Conseil de prud'hommes",
    },
    "rectorat": {
        "description": "Rectorat",
        "searches": ["académie"],
    },
    "sdsei": {
        "description": "Services départementaux des solidarités et de l'insertion",
    },
    "sie": {
        "description": "Service des impôts des entreprises du Centre des finances publiques",
        "searches": ["impots"],
    },
    "sip": {
        "description": "Service des impôts des particuliers du Centre des finances publiques",
        "searches": ["impots"],
    },
    "spip": {
        "description": "Service pénitentiaire d'insertion et de probation",
    },
    "suio": {
        "description": "Service universitaire d'information et d'orientation",
    },
    "ta": {
        "description": "Tribunal administratif",
    },
    "te": {
        "description": "Tribunal pour enfants",
    },
    "tgi": {
        "description": "Tribunal de grande instance",
    },
    "ti": {
        "description": "Tribunal d'instance",
    },
    "tresorerie": {
        "description": "Trésorerie",
    },
    "tribunal_commerce": {
        "description": "Tribunal de commerce",
    },
    "urssaf": {
        "description": "Urssaf",
        "searches": ["impots", "entreprise"],
    },
}


def clean_commune(string):
    try:
        return string.split("Cedex", 1)[0].strip()
    except Exception:
        return string


def clean_coordonnees(coords):
    if not coords:
        return None
    if len(coords) != 2:
        return None
    if type(coords[0]) != float or type(coords[1]) != float:
        return None
    return coords


def get_type_choices():
    return list(TYPES.items())


def parse_etablissement(feature):
    properties = feature.get("properties", {})

    # Coordonnées géographiques
    geometry = feature.get("geometry")
    if not geometry:
        logger.error("L'enregistrement ne possède pas de coordonnées géographiques")
        return None

    coordonnees = clean_coordonnees(geometry.get("coordinates"))
    if not coordonnees:
        logger.error("Les coordonnées géographiques sont invalides")
        return None

    # Adresses et lignes d'adresse
    adresses = properties.get("adresses", [])
    if len(adresses) == 0:
        raise RuntimeError("L'enregistrement ne possède aucune adresse")
    adresse = adresses[0]
    code_insee = properties.get("codeInsee")
    commune = Commune.objects.filter(code_insee=code_insee).first()
    if commune:
        commune_nom = commune.nom
        commune_code_postal = commune.code_postaux[0]
    else:
        commune_nom = clean_commune(adresse.get("commune"))
        commune_code_postal = adresse.get("codePostal")

    lignes = adresse.get("lignes", [])
    if len(lignes) == 0:
        raise RuntimeError("L'enregistrement ne possède aucune ligne d'adresse")

    (numero, voie) = text.extract_numero_voie(lignes[0])

    # Validation de la valeur d'adresse email
    email = properties.get("email")
    email = email if email and "@" in email else None

    # Activité
    activite = Activite.objects.filter(
        slug="mairie"
        if properties.get("pivotLocal") == "mairie"
        else "administration-publique"
    ).first()
    activite_id = activite.pk if activite else None

    return dict(
        source="public_erp",
        source_id=properties.get("id"),
        actif=True,
        coordonnees=coordonnees,
        naf=None,
        activite=activite_id,
        nom=properties.get("nom"),
        siret=None,
        numero=numero.strip().replace(",", "") if numero else None,
        voie=voie.strip(),
        lieu_dit=lignes[1] if len(lignes) > 1 else None,
        code_postal=commune_code_postal,
        commune=commune_nom,
        code_insee=code_insee,
        contact_email=email,
        telephone=properties.get("telephone"),
        site_internet=properties.get("url"),
    )


def request(path, params=None):
    try:
        res = requests.get(f"{BASE_URL}/{path}", params)
        logger.info(f"public_erp api call: {res.url}")
        if res.status_code != 200:
            raise RuntimeError(
                f"Erreur HTTP {res.status_code} lors de la requête: {res.url}"
            )
        return res.json()
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"public_erp api error: {err}")


def search_types(type, code_insee):
    if type not in TYPES:
        raise RuntimeError(f'Le type "{type}" est invalide.')
    response = request(f"communes/{code_insee}/{type}")
    try:
        results = []
        for feature in response["features"]:
            try:
                results.append(parse_etablissement(feature))
            except RuntimeError as err:
                logger.error(err)
                continue
        return results
    except (AttributeError, KeyError, IndexError, TypeError) as err:
        raise RuntimeError(f"Impossible de récupérer les résultats: {err}")


def find_public_types(terms):
    results = []
    clean = text.remove_accents(terms).lower()
    for key, val in TYPES.items():
        searches = [key, val["description"]] + val.get("searches", [])
        (found, score) = fuzzy_process.extractOne(clean, searches)
        results.append({"score": score, "type": key})
    _sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return [r["type"] for r in _sorted if r["score"] > MIN_SCORE][:MAX_TYPES]


def query(terms, code_insee):
    results = []
    found_public_types = find_public_types(terms)
    for public_type in found_public_types:
        try:
            type_results = search_types(public_type, code_insee)
            for result in type_results:
                if result and code_insee == result["code_insee"]:
                    results.append(result)
        except RuntimeError as err:
            logger.error(err)
            pass
    return results


def search(terms, code_insee):
    try:
        return query(terms, code_insee)
    except RuntimeError as err:
        logger.error(err)
        return []
