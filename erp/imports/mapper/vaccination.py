from datetime import datetime

from django.contrib.gis.geos import Point
from django.db.utils import DataError

from core.lib import text
from erp.models import Accessibilite, Activite, Commune, Erp
from erp.provider import arrondissements

RAISON_EN_ATTENTE = "En attente d'affectation"
RAISON_EQUIPE_MOBILE = "Équipe mobile écartée"
RAISON_PUBLIC_RESTREINT = "Réservé à un public restreint"
RAISON_RESERVE_PS = "Réservé aux professionnels de santé"
RAISON_RESERVE_CARCERAL = "Centre réservé à la population carcérale"


class VaccinationMapper:
    activite = Activite.objects.get(slug="centre-de-vaccination")
    discarded = False
    erp = None

    FIELDS_MAP = {
        "c_nom": "nom",
        "c_adr_num": "numero",
        "c_adr_voie": "voie",
        "c_com_nom": "commune",
        "c_com_cp": "code_postal",
        "c_com_insee": "code_insee",
        "c_rdv_tel": "telephone",
    }

    TESTS_ECARTEMENT = {
        # Réservé aux professionnels de santé
        "R\u00e9serv\u00e9 aux professionnels de sant\u00e9": RAISON_RESERVE_PS,
        "Uniquement pour les professionnels de sant\u00e9": RAISON_RESERVE_PS,
        "Ouvert uniquement aux professionnels": RAISON_RESERVE_PS,
        "Professionnels de santé uniquement": RAISON_RESERVE_PS,
        "Réservé PS": RAISON_RESERVE_PS,
        "réservé aux professionnels": RAISON_RESERVE_PS,
        "centre pour professionnels de santé": RAISON_RESERVE_PS,
        # Équipes mobiles
        "Équipe mobile": RAISON_EQUIPE_MOBILE,
        "vaccination mobile": RAISON_EQUIPE_MOBILE,
        "EMV": RAISON_EQUIPE_MOBILE,
        # En attente d'affectation
        "en attente": RAISON_EN_ATTENTE,
        # Centres réservés à la population carcérale
        "centre de détention": RAISON_RESERVE_CARCERAL,
        "pénitentiaire": RAISON_RESERVE_CARCERAL,
        "prison": RAISON_RESERVE_CARCERAL,
        "UHSA": RAISON_RESERVE_CARCERAL,
        "UHSI": RAISON_RESERVE_CARCERAL,
        "USMP": RAISON_RESERVE_CARCERAL,
    }

    def __init__(self, record, today=None):
        self.record = record
        self.erp = None
        self.geometry = None
        self.props = None
        self.today = today if today is not None else datetime.today()

    @property
    def source_id(self):
        value = self.props.get("c_gid")
        if value is None:
            raise RuntimeError("Champ c_gid manquant")
        return str(value)

    @property
    def erp_exists(self):
        return self.erp and self.erp.id is not None

    def process(self):
        try:
            self.geometry = self.record["geometry"]
            self.props = self.record["properties"]
        except KeyError as err:
            raise RuntimeError(f"Propriété manquante {err}: {self.record}")
        # Clean string properties
        for key, val in self.props.items():
            self.props[key] = text.strip_if_str(val)

        "Procède aux vérifications et à l'import de l'enregistrement"
        # Création ou récupération d'un ERP existant
        self._fetch_or_create_erp()
        self._check_importable()
        self._import_basic_erp_fields()
        self._import_coordinates()
        # Commune checks and normalization
        self._retrieve_commune_ext()
        # Strange/invalid phone numbers
        if self.erp.telephone and len(self.erp.telephone) > 20:
            self.erp.telephone = None
        # Build metadata
        self.erp.metadata = self._build_metadata()
        # Prepare comment
        commentaire = self._build_commentaire()

        try:
            # Save erp instance
            self.erp.published = True

            # Attach an Accessibilite to newly created Erps
            if not self.erp.has_accessibilite():
                accessibilite = Accessibilite(erp=self.erp)
                accessibilite.commentaire = commentaire
        except DataError as err:
            raise RuntimeError(f"Erreur à l'enregistrement des données: {err}") from err

        # FIXME: discard erps when they're no more listed in the datagouv dataset
        return (self.erp, self.discarded)

    def _build_commentaire(self):
        "Retourne un commentaire informatif à propos de l'import"
        date = self.today.strftime("%d/%m/%Y")
        return (
            f"Ces informations ont été {'mises à jour' if self.erp_exists else 'importées'} depuis data.gouv.fr le {date} "
            "https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"
        )

    def _build_metadata(self):
        url_rdv = self.props.get("c_rdv_site_web", "")
        return {
            "ban_addresse_id": self.props.get("c_id_adr"),
            "centre_vaccination": {
                "datemaj": self.props.get("c__edit_datemaj"),
                "structure": {
                    "nom": self.props.get("c_structure_rais"),
                    "numero": self.props.get("c_structure_num"),
                    "voie": self.props.get("c_structure_voie"),
                    "code_postal": self.props.get("c_structure_cp"),
                    "code_insee": self.props.get("c_structure_insee"),
                    "commune": self.props.get("c_structure_com"),
                },
                "date_fermeture": self.props.get("c_date_fermeture"),
                "date_ouverture": self.props.get("c_date_ouverture"),
                "acces_sur_rdv": self.props.get("c_rdv"),
                "url_rdv": url_rdv if url_rdv and url_rdv.startswith("http") else None,
                "modalites": self.props.get("c_rdv_modalites"),
                "prevaccination": self.props.get("c_rdv_consultation_prevaccination"),
                "horaires_rdv": {
                    "lundi": self.props.get("c_rdv_lundi") or "N/C",
                    "mardi": self.props.get("c_rdv_mardi") or "N/C",
                    "mercredi": self.props.get("c_rdv_mercredi") or "N/C",
                    "jeudi": self.props.get("c_rdv_jeudi") or "N/C",
                    "vendredi": self.props.get("c_rdv_vendredi") or "N/C",
                    "samedi": self.props.get("c_rdv_samedi") or "N/C",
                    "dimanche": self.props.get("c_rdv_dimanche") or "N/C",
                },
            },
        }

    def _check_closed(self):
        "Vérification si centre déjà fermé"
        raw_date_fermeture = self.props.get("c_date_fermeture")
        if raw_date_fermeture:
            date_fermeture = datetime.strptime(raw_date_fermeture, "%Y-%m-%d")
            if date_fermeture < self.today:
                return date_fermeture

    def _check_ecartement(self):
        "Vérification des autres raisons d'écartement"

        for (test, raison) in self.TESTS_ECARTEMENT.items():
            if text.contains_sequence(
                test, self.props.get("c_nom")
            ) or text.contains_sequence(test, self.props.get("c_rdv_modalites")):
                return raison

        if self.props.get("c_reserve_professionels_sante") is True:
            return RAISON_RESERVE_PS

        if self.props.get("c_centre_fermeture") is True:
            return RAISON_PUBLIC_RESTREINT

    def _check_importable(self):
        "Vérifications d'exclusion d'import ou de mise à jour"
        ferme_depuis = self._check_closed()
        if ferme_depuis:
            self._discard(f"Centre fermé le {ferme_depuis}")

        raison_ecartement = self._check_ecartement()
        if raison_ecartement:
            self._discard(raison_ecartement)

    def _discard(self, msg):
        "Écarte cet enregistrement de l'import, et dépublie l'Erp existant en base si besoin"
        if self.erp_exists:
            self.erp.published = False
            self.erp.save()
            msg = "MIS HORS LIGNE: " + msg
        else:
            msg = "ÉCARTÉ: " + msg
        raise RuntimeError(msg)

    def _fetch_or_create_erp(self):
        "Récupère l'Erp existant correspondant à cet enregistrement ou en crée un s'il n'existe pas"
        erp = Erp.objects.find_by_source_id(Erp.SOURCE_VACCINATION, self.source_id)
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_VACCINATION,
                source_id=self.source_id,
                activite=self.activite,
            )
        self.erp = erp

    def _import_basic_erp_fields(self):
        "Importe les champs administratif basiques du centre de vaccination"
        for (json_field, model_field) in self.FIELDS_MAP.items():
            setattr(self.erp, model_field, self.props[json_field])

    def _import_coordinates(self):
        "Importe les coordonnées géographiques du centre de vaccination"
        try:
            (lon, lat) = self.geometry["coordinates"][0]
            self.erp.geom = Point(lon, lat)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")

    def _retrieve_commune_ext(self):
        "Assigne une commune normalisée à l'Erp en cours de génération"
        if self.erp.code_insee:
            commune_ext = Commune.objects.filter(code_insee=self.erp.code_insee).first()
            if not commune_ext:
                arrdt = arrondissements.get_by_code_insee(self.erp.code_insee)
                if arrdt:
                    commune_ext = Commune.objects.filter(
                        nom__iexact=arrdt["commune"]
                    ).first()
        elif self.erp.code_postal:
            commune_ext = Commune.objects.filter(
                code_postaux__contains=[self.erp.code_postal]
            ).first()
        else:
            raise RuntimeError(
                f"Champ code_insee et code_postal nuls (commune: {self.erp.commune})"
            )

        if not commune_ext:
            raise RuntimeError("Impossible de résoudre la commune")

        self.erp.commune_ext = commune_ext
        self.erp.commune = commune_ext.nom
