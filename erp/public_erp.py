import logging
import requests

from .models import Activite, Commune

logger = logging.getLogger(__name__)

BASE_URL = "https://etablissements-publics.api.gouv.fr/v3"

TYPES = {
    "accompagnement_personnes_agees": "Plateforme d'accompagnement et de répit "
    "pour les aidants de personnes âgées",
    "adil": "Information sur le logement (agenceAgence départementale pour "
    "l'information sur le logement (ADIL) départementale, Adil)",
    "afpa": "Association nationale pour la formation professionnelle des adultes "
    "(AFPA), réseau local",
    "anah": "Agence nationale de l'habitat (ANAH), réseau local",
    "apec": "Association pour l'emploi des cadres (APEC)",
    "apecita": "Association pour l'emploi des cadres, ingénieurs et techniciens "
    "de l'agriculture et de l'agroalimentaire (APECITA), réseau local",
    "ars_antenne": "Délégation territoriale de l'Agence régionale de santé",
    "banque_de_france": "Banque de France, succursale",
    "bav": "Bureau d'aide aux victimes",
    "bsn": "Bureau ou centre du service national",
    "caa": "Cour administrative d'appel",
    "caf": "Caisse d'allocations familiales (CAF)",
    "carsat": "Caisse d'assurance retraite et de la santé au travail (CARSAT)",
    "ccas": "Centre communal d'action sociale",
    "cci": "Chambre de commerce et d'industrie (CCI)",
    "cdas": "Centre départemental d'action sociale",
    "cdg": "Centre de gestion de la fonction publique territoriale",
    "centre_detention": "Centre de détention",
    "centre_impots_fonciers": "Centre des impôts foncier et cadastre",
    "centre_penitentiaire": "Centre pénitentiaire",
    "centre_social": "Centre social",
    "cg": "Conseil départemental",
    "chambre_agriculture": "Chambre d'agriculture",
    "chambre_metier": "Chambre de métiers et de l'artisanat",
    "cicas": "Centre d'information de conseil et d'accueil des salariés (CICAS)",
    "cidf": "Centre d'information sur les droits des femmes et des familles " "(CIDFF)",
    "cij": "Information jeunesse, réseau local",
    "cio": "Centre d'information et d'orientation (CIO)",
    "civi": "Commission d'indemnisation des victimes d'infraction",
    "clic": "Point d'information local dédié aux personnes âgées",
    "cnfpt": "Centre national de la fonction publique territoriale (CNFPT), "
    "réseau local",
    "commissariat_police": "Commissariat de police",
    "commission_conciliation": "Commission départementale de conciliation",
    "conciliateur_fiscal": "Conciliateur fiscal",
    "cour_appel": "Cour d'appel",
    "cpam": "Caisse primaire d'assurance maladie (CPAM)",
    "cr": "Conseil régional",
    "crib": "Centre de ressources et d'information des bénévoles (CRIB)",
    "crous": "CROUS et ses antennes",
    "csl": "Centre de semi-liberté",
    "ddcs": "Direction départementale de la cohésion sociale (DDCS)",
    "ddcspp": "Direction départementale de la cohésion sociale et de la "
    "protection des populations (DDCSPP)",
    "ddpp": "Protection des populations (direction départementale, DDPP)",
    "ddt": "Direction départementale des territoires -et de la mer- (DDT)",
    "direccte_ut": "Unité territoriale - Direction régionale des entreprises, de "
    "la concurrence, de la consommation, du travail et de l'emploi",
    "dml": "Délégation à la mer et au littoral",
    "drac": "Direction régionale des affaires culturelles (DRAC)",
    "draf": "Direction régionale de l'alimentation, de l'agriculture et de la "
    "forêt (DRAAF)",
    "drddi": "Direction interrégionale et régionale des douanes",
    "dreal": "Direction régionale de l'environnement, de l'aménagement et du "
    "logement (DREAL)",
    "dreal_ut": "Unité territoriale - Direction régionale de l'environnement, de "
    "l'aménagement et du logement (DREAL)",
    "driea_ut": "Unité territoriale - Direction régionale et interdépartementale "
    "de l'équipement et de l'aménagement (DRIEA)",
    "edas": "Établissement départemental d'actions sociales",
    "epci": "Intercommunalité",
    "esm": "Etablissement spécialisé pour mineurs",
    "fdapp": "Fédération départementale pour la pêche et la protection du milieu "
    "aquatique",
    "fdc": "Fédération départementale des chasseurs",
    "gendarmerie": "Brigade de gendarmerie",
    "greta": "Greta",
    "hypotheque": "Service de publicité foncière ex-conservation des hypothèques",
    "inspection_academique": "Direction des services départementaux de "
    "l'Éducation nationale",
    "maia": "Mission d'accueil et d'information des associations (MAIA)",
    "mairie": "Mairie",
    "mairie_com": "Mairie des collectivités d'outre-mer",
    "mairie_mobile": "Mairie mobile de la ville de Paris",
    "maison_arret": "Maison d'arrêt",
    "maison_centrale": "Maison centrale",
    "maison_handicapees": "Maison départementale des personnes handicapées (MDPH)",
    "mds": "Maison départementale des solidarités",
    "mission_locale": "Mission locale et Permanence d'accueil, d'information et "
    "d'orientation (PAIO)",
    "mjd": "Maison de justice et du droit",
    "msa": "Mutualité sociale agricole (MSA), réseau local",
    "ofii": "Office français de l'immigration et de l'intégration (ex ANAEM), "
    "réseau local",
    "onac": "Office national des anciens combattants (ONAC), réseau local",
    "paris_mairie": "Mairie de Paris, Hôtel de Ville",
    "paris_ppp": "Préfecture de police de Paris",
    "paris_ppp_antenne": "Préfecture de police de Paris, antenne d'arrondissement",
    "paris_ppp_certificat_immatriculation": "Préfecture de police de Paris, "
    "certificat d'immatriculation",
    "paris_ppp_gesvres": "Préfecture de police de Paris - Site central de Gesvres",
    "paris_ppp_permis_conduire": "Préfecture de police de Paris, permis de " "conduire",
    "permanence_juridique": "Permanence juridique",
    "pif": "Point info famille",
    "pmi": "Centre de protection maternelle et infantile (PMI)",
    "pole_emploi": "Pôle emploi",
    "prefecture": "Préfecture",
    "prefecture_greffe_associations": "Greffe des associations",
    "prefecture_region": "Préfecture de région",
    "prudhommes": "Conseil de prud'hommes",
    "rectorat": "Rectorat",
    "sdsei": "Services départementaux des solidarités et de l'insertion",
    "sie": "Service des impôts des entreprises du Centre des finances publiques",
    "sip": "Service des impôts des particuliers du Centre des finances publiques",
    "sous_pref": "Sous-préfecture",
    "spip": "Service pénitentiaire d'insertion et de probation",
    "suio": "Service universitaire d'information et d'orientation",
    "ta": "Tribunal administratif",
    "te": "Tribunal pour enfants",
    "tgi": "Tribunal de grande instance",
    "ti": "Tribunal d'instance",
    "tresorerie": "Trésorerie",
    "tribunal_commerce": "Tribunal de commerce",
    "urssaf": "Urssaf",
}


def clean_commune(string):
    try:
        return string.split("Cedex", 1)[0].strip()
    except Exception:
        return string


def contains_numbers(string):
    return any(i.isdigit() for i in string)


def extract_numero_voie(string):
    if contains_numbers(string):
        return tuple(string.split(" ", maxsplit=1))
    else:
        return (None, string)


def parse_feature(feature):
    properties = feature.get("properties", {})

    # Coordonnées géographiques
    geometry = feature.get("geometry")
    if not geometry:
        logger.error("L'enregistrement ne possède pas de coordonnées géographiques")
        return None
    coordonnees = geometry.get("coordinates")

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

    (numero, voie) = extract_numero_voie(lignes[0])

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


def get_code_insee_type(code_insee, type):
    if type not in TYPES:
        raise RuntimeError(f'Le type "{type}" est invalide.')
    response = get(f"{BASE_URL}/communes/{code_insee}/{type}")
    results = []
    try:
        for feature in response["features"]:
            try:
                results.append(parse_feature(feature))
            except RuntimeError as err:
                logger.error(err)
                continue
        if len(results) == 0:
            raise RuntimeError("Aucun résultat.")
        return results
    except (KeyError, IndexError, TypeError) as err:
        logger.error(err)
        raise RuntimeError("Impossible de récupérer les résultats.")


def get(url, params=None):
    try:
        res = requests.get(url, params)
        logger.info(f"Public ERP api call: {res.url}")
        if res.status_code != 200:
            raise RuntimeError(f"Erreur HTTP {res.status_code} lors de la requête.")
        return res.json()
    except requests.exceptions.RequestException:
        raise RuntimeError("Annuaire des établissements publics indisponible.")
