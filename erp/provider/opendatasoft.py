import logging

import requests

from core.lib import text
from erp.provider import arrondissements

logger = logging.getLogger(__name__)

BASE_API_URL = "https://public.opendatasoft.com/api/records/1.0"
MAX_PER_PAGE = 5


def extract_coordonnes(etablissement):
    coords = etablissement.get("geolocetablissement")
    if coords and len(coords) == 2:
        return [coords[1], coords[0]]


def extract_personne_physique(etablissement):
    pseudonyme = etablissement.get("pseudonymeunitelegale")
    if pseudonyme:
        return pseudonyme
    prenom = etablissement.get("prenomusuelunitelegale", "") or etablissement.get("prenom1unitelegale", "")
    nom = etablissement.get("nomunitelegale", "")
    nom_usage = etablissement.get("nomusageunitelegale", "")
    if nom_usage:
        nom = f"{nom} ({nom_usage})"
    if not prenom and not nom:
        return None
    return f"{prenom} {nom}".strip()


def extract_nom(etablissement):
    return text.normalize_nom(
        etablissement.get("denominationusuelle1unitelegale")
        or etablissement.get("enseigne1etablissement")
        or etablissement.get("denominationusuelleetablissement")
        or etablissement.get("denominationunitelegale")
        or etablissement.get("l1_adressage_unitelegale")
        or extract_personne_physique(etablissement)
        or ""
    )


def extract_voie(etablissement):
    type_voie = etablissement.get("typevoieetablissement")
    nom_voie = etablissement.get("libellevoieetablissement")
    return f"{type_voie} {nom_voie}" if type_voie else nom_voie


def parse_etablissement(record):
    # The sirene dataset sometimes contains partially exposed info ([ND] = non diffusée), these records can be ignored
    etablissement = record.get("fields")
    if any(etablissement.get(x) == "[ND]" for x in ("codepostaletablissement", "libellecommuneetablissement")):
        return None

    nom = extract_nom(etablissement)
    if nom.upper() in ("", "[ND]"):
        return None

    voie = extract_voie(etablissement)
    return dict(
        source="opendatasoft",
        source_id=record.get("recordid"),
        coordonnees=extract_coordonnes(etablissement),
        naf=etablissement.get("activiteprincipaleetablissement"),
        activite=None,  # Would be nice to infer activite from NAF
        nom=nom,
        siret=etablissement.get("siret"),
        numero=etablissement.get("numerovoieetablissement"),
        voie=voie,
        lieu_dit=etablissement.get("complementadresseetablissement"),
        code_postal=etablissement.get("codepostaletablissement"),
        commune=etablissement.get("libellecommuneetablissement"),
        code_insee=str(etablissement.get("codecommuneetablissement") or ""),
    )


def get_district_search(code_insee):
    # In case we search in a global commune code insee which has districts
    # (arrondissements: Paris, Marseille, Lyon), prefer searching with the
    # commune name rather than the INSEE code, for accuracy.
    arrdt = arrondissements.get_by_code_insee(code_insee)
    if arrdt:
        return arrdt["commune"]
    elif code_insee == "75056":
        return "Paris"
    elif code_insee == "13055":
        return "Marseille"
    elif code_insee == "69123":
        return "Lyon"


def build_query_params(terms, code_insee):
    params = {
        "dataset": "economicref-france-sirene-v3",
        "q": terms,
        "rows": MAX_PER_PAGE,
        "refine.etatadministratifetablissement": "Actif",
        "sort": "datederniertraitementetablissement",
    }

    district_search = get_district_search(code_insee)
    if district_search:
        params["q"] = f"{terms} {district_search}"
    else:
        params["refine.codecommuneetablissement"] = code_insee

    return params


def query(terms, code_insee):
    try:
        res = requests.get(f"{BASE_API_URL}/search/", build_query_params(terms, code_insee), timeout=5)
        logger.info(f"opendatasoft api search call: {res.url}")
        if res.status_code == 404:
            if "Unknown dataset" in (error := res.json().get("error", "")):
                raise RuntimeError(f"opendatasoft: {error}")
            return []
        elif res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête: {res.url}")
        json_value = res.json()
        if not json_value or "records" not in json_value:
            raise RuntimeError(f"Résultat invalide: {json_value}")
        # FIXME: discard any parsed etablissement being None
        return [parsed for r in json_value["records"] if (parsed := parse_etablissement(r))]
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"opendatasoft search api error: {err}")


def search(terms, code_insee):
    try:
        return query(terms, code_insee)
    except RuntimeError as err:
        logger.error(err)
        return []
