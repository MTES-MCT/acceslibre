import logging
import requests
import unicodedata

from erp.models import Commune

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


def format_naf(string):
    if not string:
        return None
    lst = list(string)
    lst.insert(2, ".")
    return "".join(lst)


def query(terms, code_insee=None):
    try:
        params = {
            "per_page": MAX_PER_PAGE,
            "page": 1,
            "code_commune": code_insee,
        }
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


def parse_etablissement(record):
    # Coordonnées geographiques
    lat = record.get("latitude")
    lon = record.get("longitude")
    coordonnees = [float(lon), float(lat)] if lat and lon else None

    # Numéro, type de voie et voie
    numero = record.get("numero_voie")
    type_voie = record.get("type_voie")
    voie = record.get("libelle_voie")
    if type_voie and voie:
        voie = f"{type_voie} {voie}"

    # Commune, code postal, code insee
    commune = record.get("libelle_commune")
    code_postal = record.get("code_postal")
    # if not code_postal or not commune:
    #     logger.error(f"Résultat invalide: {record}")
    #     raise RuntimeError("Pas d'adresse valide pour ce résultat")
    code_insee = record.get("departement_commune_siege")
    if not code_insee:
        code_insee_list = Commune.objects.filter(
            code_postaux__contains=[code_postal], nom__iexact=commune
        ).values("code_insee")
        code_insee = (
            code_insee_list[0]["code_insee"] if len(code_insee_list) > 0 else None
        )
    else:
        # FIXME: arrondissements pas pris en compte
        commune_ext = Commune.objects.filter(code_insee=code_insee).first()
        commune = commune_ext.nom if commune_ext else commune

    # Raison sociale
    nom = (
        record.get("enseigne")
        or record.get("l1_normalisee")
        or record.get("nom_raison_sociale")
        or None
    )

    # Code NAF
    naf = format_naf(record.get("activite_principale_entreprise"))

    # Email
    email = record.get("email")
    email = email if email and "@" in email else None

    # Indentifiant dans la source
    source_id = str(record.get("id"))
    if not source_id:
        source_id = "-".join(
            str(x) for x in [code_postal, nom, naf, commune] if x is not None
        )

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


def search(terms, code_insee=None):
    terms = clean_search_terms(terms)
    if not terms:
        raise RuntimeError("La recherche est vide.")
    response = query(terms, code_insee=code_insee)
    results = []
    try:
        for etablissement in response["etablissement"]:
            try:
                results.append(parse_etablissement(etablissement))
            except RuntimeError as err:
                logger.error(err)
                continue
        if len(results) == 0:
            raise RuntimeError("Aucun résultat.")
        return results
    except (AttributeError, KeyError, IndexError, TypeError) as err:
        logger.error(err)
        raise RuntimeError("Impossible de récupérer les résultats.")
