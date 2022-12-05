import logging

import requests

from core.lib import text
from erp.models import Commune
from erp.provider import arrondissements, voies

logger = logging.getLogger(__name__)

# Note: Nous utilisons le endpoint v1 qui n'est pas vraiment déprécié (source Etalab).
# C'est le seul endpoint qui permette la recherche full text.
BASE_URL_V1 = "https://entreprise.data.gouv.fr/api/sirene/v1"
# Note: En revanche nous utilisons le endpoint v3 pour la qualité des données dans les
# réponses fournies.
BASE_URL_V3 = "https://entreprise.data.gouv.fr/api/sirene/v3"
MAX_PER_PAGE = 5


def clean_search_terms(string):
    # Note: search doesn't work well with accented letters...
    string = str(string).strip()
    return text.remove_accents(string.replace("/", " ")).upper()


def strip_list(lst):
    return [x for x in list(map(lambda x: x.strip(), lst)) if x != ""]


def format_coordonnees(record):
    lat = record.get("latitude")
    lon = record.get("longitude")
    return [float(lon), float(lat)] if lat and lon else None


def format_email(record):
    email = record.get("email")
    return email if email and "@" in email else None


def format_naf(record):
    naf = record.get("activite_principale") or record.get("activite_principale_entreprise")
    if not naf:
        return None
    if "." not in naf:
        lst = list(naf)
        lst.insert(2, ".")
        return "".join(lst)
    return naf


def format_personne(unite_legale):
    prenom = unite_legale.get("prenom_usuel") or unite_legale.get("prenom_1")
    nom = unite_legale.get("nom_usage") or unite_legale.get("nom")
    if prenom and nom:
        return f"{prenom} {nom}"


def format_nom(record):
    unite_legale = record.get("unite_legale", {})
    nom = (
        record.get("denomination_usuelle")
        or record.get("enseigne_1")
        or record.get("enseigne_2")
        or record.get("enseigne_3")
        or unite_legale.get("denomination")
        or unite_legale.get("denomination_usuelle_1")
        or unite_legale.get("denomination_usuelle_2")
        or unite_legale.get("denomination_usuelle_3")
        or format_personne(unite_legale)
        or None
    )
    if nom:
        nom = text.normalize_nom(nom)
    return nom


def format_source_id(record, fields=None):
    source_id = str(record.get("id")) if record.get("id") else None
    if not source_id and isinstance(fields, list) and len(fields) > 0:
        source_id = "-".join(str(x).lower() for x in fields if x is not None)
    if not source_id:
        logger.error(f"Impossible de générer une source_id: {record}")
        raise RuntimeError("Erreur lors du traitement des résultats.")
    return source_id


def retrieve_code_insee(record):
    code_insee = record.get("code_commune")
    if code_insee and len(code_insee) == 5:
        return code_insee

    commune = record.get("libelle_commune")
    code_postal = record.get("code_postal")
    if not commune or not code_postal:
        return None

    code_insee_list = Commune.objects.filter(
        code_postaux__contains=[code_postal], nom__unaccent__iexact=commune
    ).values("code_insee")

    return code_insee_list[0]["code_insee"] if len(code_insee_list) > 0 else None


def extract_geo_adresse(geo_adresse, code_postal):
    if not geo_adresse:
        return None
    try:
        parts = strip_list(geo_adresse.split(code_postal))
        if len(parts) < 2:
            return None
        addr_parts = strip_list(parts[0].split(" "))
        if text.contains_digits(addr_parts[0]):
            numero = addr_parts[0]
            rest = addr_parts[1:]
            if rest[0].lower() in ["b", "bis", "t", "ter", "q", "quater"]:
                numero = f"{numero} {rest[0]}"
                voie = " ".join(rest[1:])
            else:
                voie = " ".join(rest)
        else:
            numero = None
            voie = parts[0]
        if parts[1]:
            commune = parts[1]
        return {
            "numero": numero,
            "voie": voie,
            "code_postal": code_postal,
            "commune": commune,
        }
    except (ValueError, IndexError, TypeError, AttributeError):
        return None


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


def parse_etablissement_v3(record):
    siret = record.get("siret")

    # Statut d'activité
    if record.get("etat_administratif") == "F":
        logger.info(f"Établissement fermé: {siret}")
        return None

    # Coordonnées geographiques
    coordonnees = format_coordonnees(record)

    # Adresse
    code_postal = record.get("code_postal")
    commune = record.get("libelle_commune")
    code_insee = retrieve_code_insee(record)
    if not code_postal or not code_insee or not commune:
        return None

    adresse_data = None
    geo_adresse = record.get("geo_adresse")
    if geo_adresse:
        adresse_data = extract_geo_adresse(geo_adresse, code_postal)
    if not adresse_data:
        adresse_data = normalize_sirene_adresse(record, code_insee)
    if not adresse_data:
        return None

    nom = format_nom(record)
    naf = format_naf(record)
    email = format_email(record)
    source_id = format_source_id(record, [code_postal, nom, naf, commune])

    return dict(
        source="entreprise_api",
        source_id=source_id,
        coordonnees=coordonnees,
        naf=naf,
        activite=None,  # Would be nice to infer activite from NAF
        nom=nom,
        siret=siret,
        numero=adresse_data.get("numero"),
        voie=adresse_data.get("voie"),
        lieu_dit=None,  # Note: this API doesn't expose this data in an actionable fashion
        code_postal=adresse_data.get("code_postal"),
        commune=adresse_data.get("commune"),
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


def search_siret_v3(siret):
    try:
        res = requests.get(f"{BASE_URL_V3}/etablissements/{siret}")
        logger.info(f"entreprise api v3 siret search call: {res.url}")
        if res.status_code == 404:
            raise RuntimeError("Aucun résultat.")
        elif res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        json_value = res.json()
        if not json_value or "etablissement" not in json_value:
            raise RuntimeError("Résultat invalide.")
        return parse_etablissement_v3(json_value["etablissement"])
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"entreprise api error: {err}")


def process_response(json_value, terms, code_insee):
    results = []
    try:
        for etablissement in json_value["etablissement"]:
            departement = etablissement.get("departement")
            if code_insee and departement != code_insee[:2]:
                # skip requesting erps outside of searched departement
                continue
            try:
                parsed = search_siret_v3(etablissement.get("siret"))
                if parsed:
                    results.append(parsed)
            except RuntimeError as err:
                logger.error(err)
                continue
        return reorder_results(results, terms)
    except (AttributeError, KeyError, IndexError, TypeError) as err:
        raise RuntimeError(f"Erreur de traitement de la réponse: {err}")


def query(terms, code_insee):
    try:
        terms = clean_search_terms(terms)
        res = requests.get(
            f"{BASE_URL_V1}/full_text/{terms}",
            {"per_page": MAX_PER_PAGE, "page": 1},
            timeout=5,
        )
        logger.info(f"entreprise api call: {res.url}")
        if res.status_code == 404:
            return []
        elif res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        return process_response(res.json(), terms, code_insee)
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"entreprise api error: {err}")
    except requests.exceptions.Timeout:
        logger.error(f"entreprise api timeout : {BASE_URL_V1}/full_text/{terms}")
        return []


def search(terms, code_insee):
    try:
        return query(terms, code_insee)
    except RuntimeError as err:
        logger.error(err)
        return []
