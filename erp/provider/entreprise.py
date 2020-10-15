import logging
import requests

from erp.models import Commune


logger = logging.getLogger(__name__)

BASE_URL = "https://entreprise.data.gouv.fr/api/sirene/v1"


def query(terms):
    try:
        res = requests.get(f"{BASE_URL}/full_text/{terms}?per_page=15&page=1")
        logger.info(f"entreprise api call: {res.url}")
        if res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        return res.json()
    except requests.exceptions.RequestException as err:
        logger.error(f"entreprise api error: {err}")
        raise RuntimeError("Annuaire des entreprise indisponible.")


def parse_etablissement(record):
    # Coordonnées geographiques
    lat = record.get("latitude")
    lon = record.get("longitude")
    coordonnees = (lon, lat) if lat and lon else None

    # Commune, code postal, code insee
    commune = record.get("libelle_commune")
    code_postal = record.get("code_postal")
    if not code_postal or not commune:
        logger.error(f"Résultat invalide: {record}")
        raise RuntimeError("Pas d'adresse valide pour ce résultat")
    code_insee_list = Commune.objects.filter(
        code_postaux__contains=[code_postal], nom__iexact=commune
    ).values("code_insee")
    if len(code_insee_list) != 1:
        raise RuntimeError(
            f"Impossible d'inférer un code insee unique pour {commune} ({code_postal})"
        )
    code_insee = code_insee_list[0]["code_insee"]

    # Raison sociale
    nom = record.get("nom_raison_sociale") or record.get("l1_normalisee") or None

    # Indentifiant dans la source
    id = str(record.get("id"))
    if not id:
        id = "-".join([nom, code_insee, commune])

    return dict(
        source="entreprise_api",
        source_id=id,
        actif=True,
        coordonnees=coordonnees,
        naf=record.get("activite_principale_entreprise"),
        activite=None,  # Would be nice to infer activite from NAF
        nom=nom,
        siret=record.get("siret"),
        numero=record.get("numero_voie"),
        voie=record.get("libelle_voie"),
        lieu_dit=None,  # Note: this API doesn't expose this data in an actionable fashion
        code_postal=code_postal,
        commune=commune,
        code_insee=code_insee,
        contact_email=record.get("email"),
        telephone=None,
        site_internet=None,
    )


def search(terms):
    if not terms.strip():
        raise RuntimeError("La recherche est vide.")
    response = query(terms)
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
