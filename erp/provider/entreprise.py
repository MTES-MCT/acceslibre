import logging

import requests

from core.lib import text
from erp.models import Commune, ExternalSource
from erp.provider import arrondissements, voies

logger = logging.getLogger(__name__)

# See api doc here: https://api.gouv.fr/documentation/api-recherche-entreprises
BASE_URL_ENTERPRISE_API = "https://recherche-entreprises.api.gouv.fr/search?mtm_campaign=acces-libre"
MAX_PER_PAGE = 5


def clean_search_terms(string):
    # Note: search doesn't work well with accented letters...
    string = str(string).strip()
    return text.remove_accents(string.replace("/", " ")).upper()


def normalize_commune(code_insee):
    # First, a cheap check if code_insee is an arrondissement
    arrondissement = arrondissements.get_by_code_insee(code_insee)
    if arrondissement:
        return arrondissement["nom"].split(" ")[0] if arrondissement else None
    # Else, a db check to retrieve the normalized commune name
    commune_ext = Commune.objects.filter(code_insee=code_insee).first()
    return commune_ext.nom if commune_ext else None


def normalize_sirene_adresse(record, code_insee):
    numero = record.get("numero_voie")
    type_voie = record.get("type_voie")
    voie = record.get("libelle_voie")
    code_postal = record.get("code_postal")
    commune = record.get("libelle_commune")
    if type_voie and voie:
        type_voie = voies.TYPES_VOIE.get(type_voie) or type_voie
        voie = f"{type_voie} {voie}"
    if code_insee:
        commune = normalize_commune(code_insee) or commune
    return {
        "numero": numero,
        "voie": voie,
        "code_postal": code_postal,
        "commune": commune,
    }


def reorder_results(results, terms):
    # The idea is to reorder results with entries having the city name or postcode
    # in the initial search terms
    lower_rank = []
    higher_rank = []
    parts = [p.lower() for p in terms.split(" ")]
    for result in results:
        commune = (result.get("commune") or "").lower()
        code_postal = (result.get("code_postal") or "").lower()
        if any([part == commune or part == code_postal for part in parts]):
            higher_rank.append(result)
        else:
            lower_rank.append(result)
    return higher_rank + lower_rank


def process_response(json_value, terms, code_insee):
    results = []
    try:
        for etablissement in json_value["results"]:
            departement = etablissement.get("siege", {}).get("departement")
            if code_insee and departement != code_insee[:2]:
                # skip requesting erps outside of searched departement
                continue

            results.append(
                {
                    "source": ExternalSource.SOURCE_API_ENTREPRISE,
                    "nom": etablissement["siege"].get("nom_commercial") or etablissement["nom_complet"],
                    "voie": etablissement["siege"]["libelle_voie"],
                    "commune": etablissement["siege"]["libelle_commune"],
                    "code_postal": etablissement["siege"]["code_postal"],
                    "lieu_dit": "",
                    "coordonnees": [etablissement["siege"]["longitude"], etablissement["siege"]["latitude"]],
                    "siret": etablissement["siege"]["siret"],
                    "code_insee": code_insee,
                    **normalize_sirene_adresse(etablissement["siege"], code_insee),
                }
            )
        return reorder_results(results, terms)
    except (AttributeError, KeyError, IndexError, TypeError) as err:
        raise RuntimeError(f"Erreur de traitement de la réponse: {err}")


def search(terms, code_insee, activities):
    try:
        terms = clean_search_terms(terms)
        payload = {
            "per_page": MAX_PER_PAGE,
            "page": 1,
            "q": terms,
            "code_insee": code_insee,
            "categorie_entreprise": "PME,ETI",
            "etat_administratif": "A",
        }
        if activities:
            payload["activite_principale"] = activities

        res = requests.get(
            f"{BASE_URL_ENTERPRISE_API}",
            payload,
            timeout=5,
        )
        logger.info(f"entreprise api call: {res.url}")
        if res.status_code == 404:
            return []
        elif res.status_code != 200:
            logger.error(f"Erreur HTTP {res.status_code} lors de la requête.")
            return []
        return process_response(res.json(), terms, code_insee)
    except requests.exceptions.Timeout:
        logger.error(f"entreprise api timeout : {BASE_URL_ENTERPRISE_API}/full_text/{terms}")
        return []
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"entreprise api error: {err}")


def check_closed(term, code_insee):
    payload = {
        "per_page": MAX_PER_PAGE,
        "page": 1,
        "q": term,
        "code_insee": code_insee,
        "categorie_entreprise": "PME,ETI",
    }
    res = requests.get(
        f"{BASE_URL_ENTERPRISE_API}",
        payload,
        timeout=5,
    )
    try:
        if not (len(results := (res.json().get("results") or [])) == 1):
            return False
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ReadTimeout):
        return False

    return results[0].get("siege", {}).get("date_fermeture") is not None
