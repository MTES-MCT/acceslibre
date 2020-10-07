import base64
import logging
import json

from api_insee import ApiInsee
from api_insee import criteria
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
UNITE_LEGALE = "uniteLegale"
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


class Fuzzy(criteria.Field):
    @property
    def representation(self):
        term = str(self.value).replace('"', "").strip()
        if " " in term or "'" in term or "-" in term:
            return f'{self.name}:"{term}"~'
        return f"{self.name}:{term}~"


class OrGroup(criteria.Base):
    "See https://github.com/ln-nicolas/api_insee/issues/3"

    def __init__(self, *criteria, **kwargs):
        self.criteria_list = criteria

    def toURLParams(self):
        inner = " OR ".join([ct.toURLParams() for ct in self.criteria_list])
        return f"({inner})"


def get_client():
    try:
        return ApiInsee(
            key=settings.INSEE_API_CLIENT_KEY, secret=settings.INSEE_API_SECRET_KEY,
        )
    except HTTPError as err:
        print(err)  # XXX find a way to log this somewhere
        raise RuntimeError("Le service INSEE est indisponible.")
    except Exception:
        # api_insee raise standard exceptions when unable to connect to the auth service ;(
        raise RuntimeError("Le service INSEE est inaccessible.")


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


def format_siret(value, separator=""):
    return siret.format(value, separator=separator)


def humanize_nom(nom):
    return nom.title()


def extract_etablissement_nom(etablissement):
    nom_parts = []
    uniteLegale = etablissement.get(UNITE_LEGALE, {})
    nom_parts.append(uniteLegale.get(NOM_ENSEIGNE3))
    # périodes et résolution du nom
    periodesEtablissement = etablissement.get(PERIODES_ETABLISSEMENT, [])
    if len(periodesEtablissement) > 0:
        nom_parts.append(periodesEtablissement[0].get(NOM_ENSEIGNE1))
        nom_parts.append(periodesEtablissement[0].get(NOM_ENSEIGNE2))
    nom_parts.append(uniteLegale.get(RAISON_SOCIALE))
    nom_parts.append(
        " ".join(
            [
                uniteLegale.get(PERSONNE_NOM) or "",
                uniteLegale.get(PERSONNE_PRENOM) or "",
            ]
        )
        .strip()
        .title()
    )
    return " ".join(
        sorted(  # required as a set might come randomly sorted
            set([part.title() for part in nom_parts if part is not None and part != ""])
        )
    )


def parse_etablissement(etablissement):
    siret = etablissement.get(SIRET)
    # unité légale
    uniteLegale = etablissement.get(UNITE_LEGALE)
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
    if settings.DEBUG:
        print("Sirene query", request.url)
    try:
        return request.get()
    except RequestExeption as err:
        logger.error(err)
        raise RuntimeError(f"Recherche impossible: {err}")
    except HTTPError as err:
        if err.code == 404:
            raise RuntimeError("Aucun résultat")
        elif err.code == 400:
            logger.error(err)
            raise RuntimeError("Recherche malformée")
        else:
            logger.error(err)
            raise RuntimeError("Le service INSEE est indisponible.")


def create_find_query(nom, lieu, naf=None):
    query = (
        criteria.Field(STATUT, "A")
        & OrGroup(criteria.FieldExact(CODE_POSTAL, lieu), Fuzzy(COMMUNE, lieu),)
        & OrGroup(
            Fuzzy(RAISON_SOCIALE, nom.upper()),
            Fuzzy(NOM_ENSEIGNE3, nom.upper()),
            Fuzzy(PERSONNE_NOM, nom.upper()),
            criteria.Periodic(Fuzzy(NOM_ENSEIGNE1, nom.upper())),
            criteria.Periodic(Fuzzy(NOM_ENSEIGNE2, nom.upper())),
        )
    )
    if naf:
        query = query & criteria.Field(ACTIVITE_NAF, f"{naf}~")
    return query


def find_etablissements(nom, code_postal, naf=None, limit=10):
    q = create_find_query(nom, code_postal, naf=naf)
    request = get_client().siret(q=q, nombre=limit, masquerValeursNulles=True,)
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
