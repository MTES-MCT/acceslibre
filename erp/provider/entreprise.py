import logging
import requests
import unicodedata

from erp.models import Commune
from erp.provider import arrondissements, sirene


logger = logging.getLogger(__name__)

BASE_URL = "https://entreprise.data.gouv.fr/api/sirene/v1"
MAX_PER_PAGE = 20


def remove_accents(input_str):
    # see https://stackoverflow.com/a/517974/330911
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def clean_search_terms(string):
    # Note: search doesn't work well with accented letters...
    string = str(string).strip()
    return remove_accents(string.replace("/", " ")).upper()


def query(terms):
    try:
        params = {"per_page": MAX_PER_PAGE, "page": 1}
        res = requests.get(f"{BASE_URL}/full_text/{terms}", params)
        logger.info(f"entreprise api call: {res.url}")
        if res.status_code == 404:
            raise RuntimeError("Aucun résultat.")
        elif res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        return res.json()
    except requests.exceptions.RequestException as err:
        logger.error(f"entreprise api error: {err}")
        raise RuntimeError("Annuaire des entreprise indisponible.")


def format_coordonnees(record):
    lat = record.get("latitude")
    lon = record.get("longitude")
    return [float(lon), float(lat)] if lat and lon else None


def format_email(record):
    email = record.get("email")
    return email if email and "@" in email else None


def format_naf(record):
    naf = record.get("activite_principale_entreprise")
    if not naf:
        return None
    lst = list(naf)
    lst.insert(2, ".")
    return "".join(lst)


def format_nom(record):
    return (
        record.get("enseigne")
        or record.get("l1_normalisee")
        or record.get("nom_raison_sociale")
        or None
    )


def format_source_id(record, fields=None):
    source_id = str(record.get("id")) if record.get("id") else None
    if not source_id and isinstance(fields, list) and len(fields) > 0:
        source_id = "-".join(str(x).lower() for x in fields if x is not None)
    if not source_id:
        raise RuntimeError(f"Impossible de générer une source_id: {record}")
    return source_id


def retrieve_code_insee(record):
    code_insee = record.get("departement_commune_siege")
    if code_insee:
        return code_insee

    commune = record.get("libelle_commune")
    code_postal = record.get("code_postal")
    if not commune or not code_postal:
        return None

    code_insee_list = Commune.objects.filter(
        code_postaux__contains=[code_postal], nom__iexact=commune
    ).values("code_insee")

    return code_insee_list[0]["code_insee"] if len(code_insee_list) > 0 else None


def normalize_commune(code_insee):
    # First, a cheap check if code_insee is an arrondissement
    arrondissement = arrondissements.get_by_code_insee(code_insee)
    if arrondissement:
        return arrondissement["nom"].split(" ")[0] if arrondissement else None
    # Else, a db check to retrieve the normalized commune name
    commune_ext = Commune.objects.filter(code_insee=code_insee).first()
    return commune_ext.nom if commune_ext else None


def parse_etablissement(record):
    # Coordonnées geographiques
    coordonnees = format_coordonnees(record)

    # Adresse
    numero = record.get("numero_voie")
    type_voie = record.get("type_voie")
    voie = record.get("libelle_voie")
    if type_voie and voie:
        voie = f"{type_voie} {voie}"

    code_postal = record.get("code_postal")
    if not code_postal:
        return None

    commune = record.get("libelle_commune")
    if not commune:
        return None

    code_insee = retrieve_code_insee(record)
    if code_insee:
        commune = normalize_commune(code_insee) or commune

    nom = format_nom(record)
    naf = format_naf(record)
    email = format_email(record)
    source_id = format_source_id(record, [code_postal, nom, naf, commune])

    return dict(
        source="entreprise_api",
        source_id=source_id,
        actif=True,
        coordonnees=coordonnees,
        naf=naf,
        activite=None,  # Would be nice to infer activite from NAF
        nom=nom,
        siret=record.get("siret"),
        numero=numero,
        voie=voie,
        lieu_dit=None,  # Note: this API doesn't expose this data in an actionable fashion
        code_postal=code_postal,
        commune=commune,
        code_insee=code_insee,
        contact_email=email,
        telephone=None,
        site_internet=None,
    )


def reorder_results(results, terms):
    # The idea is to reorder results with entries having the city name or postcode
    # in the initial search terms
    lower_rank = []
    higher_rank = []
    parts = [p.lower() for p in terms.split(" ")]
    for result in results:
        commune = result["commune"].lower()
        code_postal = result["code_postal"].lower()
        if any([part == commune or part == code_postal for part in parts]):
            higher_rank.append(result)
        else:
            lower_rank.append(result)
    return higher_rank + lower_rank


def search(terms):
    terms = clean_search_terms(terms)
    if not terms:
        raise RuntimeError("La recherche est vide.")

    # search for siret, if any provided
    siret = next((x for x in terms.split(" ") if sirene.validate_siret(x)), None)
    if siret:
        try:
            siret_result = search_siret(siret)
        except RuntimeError as err:
            logger.debug(f"Pas de résultat pour siret={siret} ({err})")
        terms = terms.replace(siret, "").strip()
        if siret_result:
            return [siret_result]

    # search for remaining terms, if any
    results = []
    if terms:
        results = results + search_fulltext(terms)
    if len(results) == 0:
        raise RuntimeError("Aucun résultat.")
    return results


def search_fulltext(terms):
    response = query(terms)
    results = []
    try:
        for etablissement in response["etablissement"]:
            try:
                parsed = parse_etablissement(etablissement)
                if parsed:
                    results.append(parsed)
            except RuntimeError as err:
                logger.error(err)
                continue
        return reorder_results(results, terms)
    except (AttributeError, KeyError, IndexError, TypeError) as err:
        logger.error(err)
        raise RuntimeError("Impossible de récupérer les résultats.")


def search_siret(siret):
    try:
        res = requests.get(f"{BASE_URL}/siret/{siret}")
        logger.info(f"entreprise api siret search call: {res.url}")
        if res.status_code == 404:
            raise RuntimeError("Aucun résultat.")
        elif res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        json_value = res.json()
        if not json_value or "etablissement" not in json_value:
            raise RuntimeError("Résultat invalide.")
        return parse_etablissement(json_value["etablissement"])
    except requests.exceptions.RequestException as err:
        logger.error(f"entreprise api error: {err}")
        raise RuntimeError("Annuaire des entreprise indisponible.")
