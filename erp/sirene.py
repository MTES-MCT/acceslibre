import base64
import logging
import json

from api_insee import ApiInsee
from api_insee.criteria import Field, Periodic
from api_insee.exeptions.request_exeption import RequestExeption
from django.conf import settings
from stdnum.fr import siret
from stdnum import exceptions as stdnum_ex
from urllib.error import HTTPError


ACTIVITE_NAF = "activitePrincipaleUniteLegale"
CODE_INSEE = "codeCommuneEtablissement"
CODE_POSTAL = "codePostalEtablissement"
COMMUNE = "libelleCommuneEtablissement"
COMPLEMENT = "complementAdresseEtablissement"
INDICE = "indiceRepetitionEtablissement"
NUMERO = "numeroVoieEtablissement"
NOM_ENSEIGNE1 = "enseigne1Etablissement"
NOM_ENSEIGNE2 = "denominationUsuelleEtablissement"
NOM_ENSEIGNE3 = "denominationUsuelle1UniteLegale"
PERIODES_ETABLISSEMENT = "periodesEtablissement"
PERSONNE_NOM = "nomUniteLegale"
PERSONNE_PRENOM = "prenomUsuelUniteLegale"
RAISON_SOCIALE = "denominationUniteLegale"
STATUT = "etatAdministratifUniteLegale"
SIRET = "siret"
TYPE_VOIE = "typeVoieEtablissement"
VOIE = "libelleVoieEtablissement"

SIRET_API_REQUEST_FIELDS = [
    ACTIVITE_NAF,
    CODE_INSEE,
    CODE_POSTAL,
    COMMUNE,
    COMPLEMENT,
    INDICE,
    NOM_ENSEIGNE1,
    NOM_ENSEIGNE2,
    NOM_ENSEIGNE3,
    NUMERO,
    PERSONNE_NOM,
    PERSONNE_PRENOM,
    RAISON_SOCIALE,
    SIRET,
    STATUT,
    TYPE_VOIE,
    VOIE,
]

SIRENE_VOIES = {
    "ALL": "Allée",
    "AV": "Avenue",
    "BD": "Boulevard",
    "CAR": "Carrefour",
    "CHE": "Chemin",
    "CHS": "Chaussée",
    "CITE": "Cité",
    "COR": "Corniche",
    "CRS": "Cours",
    "DOM": "Domaine",
    "DSC": "Descente",
    "ECA": "Ecart",
    "ESP": "Esplanade",
    "FG": "Faubourg",
    "GR": "Grande Rue",
    "HAM": "Hameau",
    "HLE": "Halle",
    "IMP": "Impasse",
    "LD": "Lieu dit",
    "LOT": "Lotissement",
    "MAR": "Marché",
    "MTE": "Montée",
    "PAS": "Passage",
    "PL": "Place",
    "PLN": "Plaine",
    "PLT": "Plateau",
    "PRO": "Promenade",
    "PRV": "Parvis",
    "QUA": "Quartier",
    "QUAI": "Quai",
    "RES": "Résidence",
    "RLE": "Ruelle",
    "ROC": "Rocade",
    "RPT": "Rond Point",
    "RTE": "Route",
    "RUE": "Rue",
    "SEN": "Sentier",
    "SQ": "Square",
    "TPL": "Terre-plein",
    "TRA": "Traverse",
    "VLA": "Villa",
    "VLGE": "Village",
}

logger = logging.getLogger(__name__)


def get_client():
    return ApiInsee(
        key=settings.INSEE_API_CLIENT_KEY, secret=settings.INSEE_API_SECRET_KEY,
    )


def base64_decode_etablissement(data):
    try:
        return json.loads(base64.urlsafe_b64decode(data).decode())
    except Exception as err:
        logger.error(err)
        raise RuntimeError("Impossible de décoder les informations de l'établissement")


def base64_encode_etablissement(etablissement):
    try:
        return base64.urlsafe_b64encode(json.dumps(etablissement).encode()).decode(
            "utf-8"
        )
    except Exception as err:
        logger.error(err)
        raise RuntimeError("Impossible d'encoder les informations de l'établissement")


def format_siret(value):
    return siret.format(value, separator="")


def extract_etablissement_nom(etablissement):
    nom = None
    uniteLegale = etablissement.get("uniteLegale")
    # périodes et résolution du nom
    # TODO: NOM_ENSEIGNE3, concat infos
    periodesEtablissement = etablissement.get(PERIODES_ETABLISSEMENT, [])
    if len(periodesEtablissement) > 0:
        nom = periodesEtablissement[0].get(NOM_ENSEIGNE1)
        if not nom:
            nom = periodesEtablissement[0].get(NOM_ENSEIGNE2)
    if not nom:
        nom = uniteLegale.get(RAISON_SOCIALE)
    if not nom:
        nom = " ".join(
            [
                uniteLegale.get(PERSONNE_NOM) or "",
                uniteLegale.get(PERSONNE_PRENOM) or "",
            ]
        ).strip()
    return nom


def parse_etablissement(etablissement):
    siret = etablissement.get(SIRET)
    # unité légale
    uniteLegale = etablissement.get("uniteLegale")
    naf = uniteLegale.get(ACTIVITE_NAF)
    # adresse
    adresseEtablissement = etablissement.get("adresseEtablissement")
    numeroVoieEtablissement = adresseEtablissement.get(NUMERO)
    indiceRepetitionEtablissement = adresseEtablissement.get(INDICE)
    typeVoieEtablissement = adresseEtablissement.get(TYPE_VOIE)
    if typeVoieEtablissement and typeVoieEtablissement in SIRENE_VOIES:
        typeVoieEtablissement = SIRENE_VOIES.get(typeVoieEtablissement)
    libelleVoieEtablissement = adresseEtablissement.get(VOIE)
    return dict(
        actif=uniteLegale.get(STATUT) == "A",
        naf=naf,
        nom=extract_etablissement_nom(etablissement),
        siret=siret,
        numero=" ".join(
            [numeroVoieEtablissement or "", indiceRepetitionEtablissement or "",]
        ).strip()
        or None,
        voie=" ".join(
            [typeVoieEtablissement or "", libelleVoieEtablissement or "",]
        ).strip()
        or None,
        lieu_dit=adresseEtablissement.get(COMPLEMENT),
        code_postal=adresseEtablissement.get(CODE_POSTAL),
        commune=adresseEtablissement.get(COMMUNE),
        code_insee=adresseEtablissement.get(CODE_INSEE),
    )


def execute_request(request):
    print(request.url)
    try:
        return request.get()
    except RequestExeption as err:
        logger.error(err)
        raise RuntimeError("Recherche impossible.")
    except HTTPError as err:
        if err.code == 404:
            raise RuntimeError("Aucun résultat")
        elif err.code == 400:
            logger.error(err)
            raise RuntimeError("Recherche malformée")
        else:
            logger.error(err)
            raise RuntimeError("Le service INSEE est indisponible.")


def find_etablissements(nom, code_postal=None, limit=5):
    nom = nom.replace('"', "")
    nom_search = f'"{nom}"~'
    if code_postal is not None:
        q = Field(CODE_POSTAL, code_postal)
    q = q & (
        Field(RAISON_SOCIALE, nom_search)
        | Field(NOM_ENSEIGNE3, nom_search)
        | Field(PERSONNE_NOM, nom_search)
        | Periodic(Field(NOM_ENSEIGNE1, nom_search))
        | Periodic(Field(NOM_ENSEIGNE2, nom_search))
    )
    request = get_client().siret(q=q, nombre=limit, masquerValeursNulles=True,)
    # FIXME: ugly temporary workaround for https://github.com/ln-nicolas/api_insee/issues/3
    request._url_params["q"] = request._url_params["q"].replace(" AND ", " AND (") + ")"
    response = execute_request(request)
    results = []
    for etablissement in response.get("etablissements", []):
        results.append(parse_etablissement(etablissement))
    if len(results) == 0:
        raise RuntimeError("Aucun résultat")
    return results


def get_siret_info(value):
    request = get_client().siret(value, champs=SIRET_API_REQUEST_FIELDS,)
    response = execute_request(request)
    return parse_etablissement(response.get("etablissement"))


def validate_siret(value):
    try:
        return siret.validate(value)
    except stdnum_ex.ValidationError:
        return None
