import logging
import requests

from core.lib import text

logger = logging.getLogger(__name__)

BASE_API_URL = "https://public.opendatasoft.com/api/records/1.0/"
MAX_PER_PAGE = 5


def extract_coordonnes(etablissement):
    coords = etablissement.get("geolocetablissement")
    if coords and len(coords) == 2:
        return [coords[1], coords[0]]


def extract_nom(etablissement):
    usage = etablissement.get("nomusageunitelegale", "") or ""
    if usage:
        usage = f" ({usage})"
    return text.normalize_nom(
        (
            etablissement.get("enseigne1etablissement")
            or etablissement.get("denominationusuelleetablissement")
            or etablissement.get("denominationunitelegale")
            or etablissement.get("l1_adressage_unitelegale")
        )
        + usage
    )


def extract_voie(etablissement):
    type_voie = etablissement.get("typevoieetablissement")
    nom_voie = etablissement.get("libellevoieetablissement")
    return f"{type_voie} {nom_voie}" if type_voie else nom_voie


def parse_etablissement(record):
    etablissement = record.get("fields")
    nom = extract_nom(etablissement)
    voie = extract_voie(etablissement)
    return dict(
        source="opendatasoft",
        source_id=record.get("recordid"),
        actif=etablissement.get("etatadministratifetablissement") == "Actif",
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
        code_insee=etablissement.get("codecommuneetablissement"),
    )


def query(terms, code_insee):
    try:
        res = requests.get(
            f"{BASE_API_URL}/search/",
            {
                "dataset": "sirene_v3",
                "q": terms,
                "rows": MAX_PER_PAGE,
                "sort": "datederniertraitementetablissement",
                "refine.codecommuneetablissement": code_insee,
                "refine.etatadministratifetablissement": "Actif",
            },
        )
        logger.info(f"opendatasoft api search call: {res.url}")
        if res.status_code == 404:
            return []
        elif res.status_code != 200:
            raise RuntimeError(
                f"Erreur HTTP {res.status_code} lors de la requête: {res.url}"
            )
        json_value = res.json()
        if not json_value or "records" not in json_value:
            raise RuntimeError(f"Résultat invalide: {json_value}")
        return [parse_etablissement(r) for r in json_value["records"]]
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"opendatasoft search api error: {err}")


def search(terms, code_insee):
    try:
        return query(terms, code_insee)
    except RuntimeError as err:
        logger.error(err)
        return []
