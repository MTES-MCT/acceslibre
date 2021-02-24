from datetime import datetime

from django.contrib.gis.geos import Point

from erp.models import Accessibilite, Commune, Erp
from erp.provider import arrondissements


class RecordMapper:
    FIELDS_MAP = {
        "c_nom": "nom",
        "c_adr_num": "numero",
        "c_adr_voie": "voie",
        "c_com_nom": "commune",
        "c_com_cp": "code_postal",
        "c_com_insee": "code_insee",
        "c_rdv_tel": "telephone",
    }

    RESERVE_PS = [
        "R\u00e9serv\u00e9 aux professionnels de sant\u00e9",
        "Uniquement pour les professionnels de sant\u00e9",
        "Ouvert uniquement aux professionnels",
    ]

    def __init__(self, record, today=None):
        self.erp = None
        self.today = today if today is not None else datetime.today()
        try:
            self.geometry = record["geometry"]
            self.props = record["properties"]
        except KeyError as err:
            raise RuntimeError(f"Propriété manquante {err}: {record}")

    @property
    def source_id(self):
        value = self.props.get("c_gid")
        if value is None:
            raise RuntimeError("Champ c_gid manquant")
        return str(value)

    @property
    def erp_exists(self):
        return self.erp and self.erp.id is not None

    def discard(self, msg):
        if self.erp_exists:
            self.erp.published = False
            self.erp.save()
            msg = "UNPUBLISHED: " + msg
        else:
            msg = "SKIPPED: " + msg
        raise RuntimeError(msg)

    def retrieve_commune_ext(self):
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

    def build_metadata(self):
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
                "url_rdv": self.props.get("c_rdv_site_web"),
                "modalites": self.props.get("c_rdv_modalites"),
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

    def build_commentaire(self):
        date = self.today.strftime("%d/%m/%Y")
        return (
            f"Ces informations ont été {'mises à jour' if self.erp_exists else 'importées'} depuis data.gouv.fr le {date} "
            "https://www.data.gouv.fr/fr/datasets/lieux-de-vaccination-contre-la-covid-19/"
        )

    def check_closed(self):
        # Exclusion des centres déjà fermés
        raw_date_fermeture = self.props.get("c_date_fermeture")
        if raw_date_fermeture:
            date_fermeture = datetime.strptime(raw_date_fermeture, "%Y-%m-%d")
            if date_fermeture < self.today:
                return date_fermeture

    def check_reserve_ps(self):
        # Exclusion des centres uniquement réservés aux personnels soignants
        modalites = self.props.get("c_rdv_modalites")
        if modalites and any(
            test.lower() in modalites.lower() for test in self.RESERVE_PS
        ):
            return modalites

    def check_equipe_mobile(self):
        # Exclusion des équipes mobiles
        modalites = self.props.get("c_rdv_modalites")
        if modalites:
            if "equipe mobile" in modalites.lower():
                return modalites

    def extract_coordinates(self):
        try:
            (lon, lat) = self.geometry["coordinates"][0]
            return Point(lon, lat)
        except (KeyError, IndexError):
            raise RuntimeError("Coordonnées géographiques manquantes ou invalides")

    def fetch_or_create_erp(self, activite):
        erp = Erp.objects.find_by_source_id(Erp.SOURCE_VACCINATION, self.source_id)
        if not erp:
            erp = Erp(
                source=Erp.SOURCE_VACCINATION,
                source_id=self.source_id,
                activite=activite,
            )
        self.erp = erp

    def check_importable(self):
        # Vérifications d'exclusion d'import ou de mise à jour
        ferme_depuis = self.check_closed()
        if ferme_depuis:
            self.discard(f"Centre fermé le {ferme_depuis}")

        reserve_ps = self.check_reserve_ps()
        if reserve_ps:
            self.discard(f"Réservé aux professionnels de santé: {reserve_ps}")

        equipe_mobile = self.check_equipe_mobile()
        if equipe_mobile:
            self.discard(f"Équipe mobile écartée: {equipe_mobile}")

    def import_basic_fields(self):
        # Import basic administrative fields
        for (json_field, model_field) in self.FIELDS_MAP.items():
            setattr(self.erp, model_field, self.props[json_field])

    def process(self, activite):
        # Création ou récupération d'un ERP existant
        self.fetch_or_create_erp(activite)
        self.check_importable()
        self.import_basic_fields()
        # Coordinates
        self.erp.geom = self.extract_coordinates()
        # Commune checks and normalization
        self.retrieve_commune_ext()
        # Strange/invalid phone numbers
        if self.erp.telephone and len(self.erp.telephone) > 20:
            self.erp.telephone = None
        # Build metadata
        self.erp.metadata = self.build_metadata()
        # Prepare comment
        commentaire = self.build_commentaire()

        # Save erp instance
        self.erp.save()

        # Attach a comment to the Accessibilite object
        if self.erp_exists and self.erp.has_accessibilite():
            accessibilite = self.erp.accessibilite
        else:
            accessibilite = Accessibilite(erp=self.erp)
        accessibilite.commentaire = commentaire
        accessibilite.save()

        return self.erp
