import logging
from datetime import datetime

from core.lib import geo
from erp.models import Accessibilite, Activite, Commune, Erp

logger = logging.getLogger(__name__)

mapping_service_public_to_acceslibre = {
    "aav": "Association aide aux victimes",
    "accompagnement_personnes_agees": "Accompagnement personnes agees",
    "ad": "Administration publique",
    "ademe": "Administration publique",
    "adil": "Agence départementale d'information sur le logement",
    "afpa": "Institut de formation",
    "agefiph": "Association de gestion du fonds pour l'insertion professionnelle des personnes handicapées",
    "anah": "Administration publique",
    "antenne_justice": "Point justice",
    "apec": "Emploi, formation",
    "apecita": "Emploi, formation",
    "aract": "Emploi, formation",
    "ars": "Administration publique",
    "ars_antenne": "Administration publique",
    "asn": "Administration publique",
    "banque_de_france": "Banques, caisses d'épargne",
    "bav": "Association aide aux victimes",
    "bdf": "Banques, caisses d'épargne",
    "bibli": "Bibliothèque médiathèque",
    "bsn": "Établissement militaire",
    "bureau_de_douane": "Bureau de douane",
    "caa": "Tribunal",
    "cadastre": "Administration publique",
    "caf": "caisse d'allocations familiales (CAF)",
    "canope_atelier": "Emploi, formation",
    "canope_dt": "Emploi, formation",
    "cap_emploi": "Emploi, formation",
    "carif_oref": "Emploi, formation",
    "carsat": "Retraite",
    "caue": "Organisme de conseil",
    "ccd": "Tribunal",
    "cci": "Chambre de commerce et d'industrie",
    "cdad": "Point justice",
    "cdg": "Emploi, formation",
    "centre_detention": "Etablissement pénitentiaire",
    "centre_impots_fonciers": "Administration publique",
    "centre_penitentiaire": "Etablissement pénitentiaire",
    "cerema": "Administration publique",
    "cesr": "Administration publique",
    "cg": "Administration publique",
    "chambre_agriculture": "Chambre agriculture",
    "chambre_metier": "Chambre metier",
    "chambre_notaires": "Notaire",
    "chu": "Hôpital",
    "cicas": "Retraite",
    "cidf": "Centre d'information sur les droits des femmes et des familles",
    "cij": "Point information jeunesse",
    "cio": "Centre d’information et d’orientation",
    "cirfa": "Établissement militaire",
    "cirgn": "Établissement militaire",
    "civi": "Tribunal",
    "clic": "Point d'information local dédié aux personnes âgées",
    "cnfpt": "Institut de formation",
    "cnra": "Administration publique",
    "commissariat_police": "Commissariat de Police",
    "commission_conciliation": "Administration publique",
    "conciliateur_fiscal": "Administration publique",
    "conseil_culture": "Administration publique",
    "cour_appel": "Tribunal",
    "cpam": "Sécurité sociale, mutuelle santé",
    "cr": "Administration publique",
    "crc": "Administration publique",
    "credit_municipal": "Banques, caisses d'épargne",
    "creps": "Institut de formation",
    "crfpn": "Institut de formation",
    "crib": "Centre de ressources et d'information",
    "crous": "Résidence, foyer",
    "crpv": "Centre médical",
    "csl": "Etablissement pénitentiaire",
    "ctrc": "Administration publique",
    "dac": "Administration publique",
    "dcf": "Administration publique",
    "dcstep": "Administration publique",
    "dd_femmes": "Administration publique",
    "dd_fip": "Administration publique",
    "ddcspp": "Administration publique",
    "ddpjj": "Administration publique",
    "ddpp": "Administration publique",
    "ddsp": "Administration publique",
    "ddt": "Administration publique",
    "ddva": "Mission d'accueil et d'information des associations",
    "did_routes": "Administration publique",
    "dir_insee": "Administration publique",
    "dir_mer": "Administration publique",
    "dir_meteo": "Administration publique",
    "dir_pj": "Administration publique",
    "direccte": "Administration publique",
    "direccte_ut": "Administration publique",
    "direction_territoriale_police": "Administration publique",
    "dmd": "Administration publique",
    "dml": "Administration publique",
    "dr_femmes": "Administration publique",
    "dr_fip": "Administration publique",
    "dr_insee": "Administration publique",
    "drac": "Administration publique",
    "draf": "Administration publique",
    "drajes": "Administration publique",
    "drari": "Administration publique",
    "drddi": "Administration publique",
    "dreal": "Administration publique",
    "dreal_ut": "Administration publique",
    "driea": "Administration publique",
    "driea_ut": "Administration publique",
    "drihl": "Administration publique",
    "drihl_ut": "Administration publique",
    "drjscs": "Administration publique",
    "droit_travail": "Administration publique",
    "dronisep": "Administration publique",
    "drpjj": "Administration publique",
    "drsp": "Administration publique",
    "dtam": "Administration publique",
    "dz_paf": "Administration publique",
    "epci": "Collectivité territoriale",
    "epide": "Administration publique",
    "esm": "Etablissement pénitentiaire",
    "espe": "Emploi, formation",
    "fdapp": "Fédération départementale pour la pêche et la protection du milieu aquatique",
    "fdc": "Association",
    "fr_renov": "Administration publique",
    "gendarmerie": "Gendarmerie",
    "gendarmerie_departementale": "Gendarmerie",
    "gendarmerie_moto": "Gendarmerie",
    "greta": "Institut de formation",
    "huissiers_justice": "Huissier",
    "hypotheque": "Administration publique",
    "inpi": "Administration publique",
    "inspection_academique": "Administration publique",
    "laboratoire_departemental": "Administration publique",
    "maia": "Administration publique",
    "mairie": "Mairie",
    "mairie_com": "Mairie",
    "maison_arret": "Etablissement pénitentiaire",
    "maison_centrale": "Etablissement pénitentiaire",
    "maison_emploi": "Emploi, formation",
    "maison_handicapees": "Maison départementale des personnes handicapées",
    "maison_metropole_lyon": "Collectivité territoriale",
    "mission_locale": "Emploi, formation",
    "mjd": "Point justice",
    "msa": "Sécurité sociale, mutuelle santé",
    "msap": "Guichet France Services",
    "ofii": "Administration publique",
    "onac": "Administration publique",
    "onf": "Administration publique",
    "ordre_avocats": "Ordre des avocats",
    "paierie_departementale": "Trésorerie",
    "paierie_regionale": "Trésorerie",
    "parc_naturel_regional": "Espace vert et naturel",
    "paris_mairie": "Mairie",
    "paris_ppp": "Administration publique",
    "paris_ppp_gesvres": "Administration publique",
    "pcb": "Point conseil budget",
    "permanence_juridique": "Point justice",
    "pif": "Centre de ressources et d'information",
    "plateforme_naturalisation": "Administration publique",
    "pmi": "Centre de protection maternelle et infantile (PMI)",
    "point_accueil_numerique": "Point accueil numerique",
    "pole_emploi": "Emploi, formation",
    "pp_marseille": "Administration publique",
    "prefecture": "Administration publique",
    "prefecture_greffe_associations": "Administration publique",
    "prefecture_region": "Administration publique",
    "prs": "Administration publique",
    "prudhommes": "Tribunal",
    "rectorat": "Administration publique",
    "rrc": "Hôpital",
    "safer": "Administration publique",
    "sdac": "Administration publique",
    "sde": "Administration publique",
    "sdis": "Administration publique",
    "sdjes": "Administration publique",
    "service_navigation": "Administration publique",
    "sgami": "Administration publique",
    "sie": "Administration publique",
    "sip": "Trésorerie",
    "sous_pref": "Administration publique",
    "spip": "Administration publique",
    "ssti": "Administration publique",
    "suio": "Emploi, formation",
    "ta": "Tribunal",
    "te": "Tribunal",
    "tgi": "Tribunal",
    "ti": "Administration publique",
    "tresorerie": "Trésorerie",
    "tribunal_commerce": "Tribunal",
    "urcaue": "Association",
    "urssaf": "Service des impôts des entreprises du centre des finances publiques",
}


class ServicePublicMapper:
    def __init__(self, record, source=None, activite=None, today=None):
        self.record = record
        self.today = today or datetime.today()
        self.activite = activite
        self.source = source

    def _extract_address(self, line):
        fields = line.get("adresse")[0]
        num = voie = lieu_dit = None

        num, voie = fields["numero_voie"].split(None, 1)
        return num, voie, lieu_dit

    def process(self):
        if not (all([key in self.record for key in ("ancien_code_pivot", "partenaire_identifiant", "nom", "adresse")])):
            return None, None

        # NOTE: we search on both gendarmerie and service_public datasets as the gendarmerie import is taking
        # ownership on all the gendarmeries even on those initially coming from the service_public import
        def _search_by_old_code(old_code):
            return Erp.objects.find_by_source_id(
                [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE], old_code, published=True
            ).first()

        def _search_by_partner_id(partner_id):
            return Erp.objects.find_by_source_id(
                [Erp.SOURCE_SERVICE_PUBLIC, Erp.SOURCE_GENDARMERIE],
                partner_id,
                published=True,
            ).first()

        def _search_by_name_address(name, address):
            postal_code = address[0]["code_postal"]
            commune = address[0]["nom_commune"]
            return (
                Erp.objects.search_what(name)
                .filter(code_postal=postal_code, commune__iexact=commune, published=True)
                .first()
            )

        erp = (
            _search_by_old_code(self.record["ancien_code_pivot"])
            or _search_by_partner_id(self.record["partenaire_identifiant"])
            or _search_by_name_address(self.record["nom"], self.record["adresse"])
        )

        commune_ext_id = Commune.objects.filter(
            code_postaux__contains=[self.record["adresse"][0]["code_postal"]]
        ).first()
        activite = mapping_service_public_to_acceslibre.get(self.record["pivot"][0]["type_service_local"])
        if not activite:
            logger.info("Ignore ERP with unknown/unmapped activity %s", self.record["privot"]["type_service_local"])
            return None, None

        if not erp:
            erp = Erp(
                nom=self.record["nom"],
                source=Erp.SOURCE_SERVICE_PUBLIC,
                source_id=self.record["ancien_code_pivot"],
                user_type=Erp.USER_ROLE_SYSTEM,
                published=False,  # will be set to True later on, if we have access info
            )
            erp.save()
            Accessibilite.objects.create(erp=erp)
        else:
            erp.nom = self.record["nom"]

        num, voie, lieu_dit = self._extract_address(self.record)
        lat = self.record["adresse"][0]["latitude"]
        long = self.record["adresse"][0]["longitude"]

        erp.telephone = self.record["telephone"][0].get("valeur").replace(" ", "")
        erp.contact_email = self.record["adresse_courriel"][0]
        erp.site_internet = self.record["site_internet"][0].get("valeur")
        erp.code_insee = self.record["code_insee_commune"]
        erp.numero = num
        erp.lieu_dit = lieu_dit
        erp.voie = voie
        erp.code_postal = self.record["adresse"][0]["code_postal"]
        erp.commune = self.record["adresse"][0]["nom_commune"]
        erp.commune_ext_id = commune_ext_id
        erp.geom = geo.parse_location((lat, long))
        erp.activite = Activite.objects.get(nom=activite)
        erp.asp_id = self.record["id"]

        access = self.record["adresse"][0]["accessibilite"]
        access_note = self.record["adresse"][0]["note_accessibilite"]
        if access:
            erp.published = True
            if access == "ACC":
                if "plain-pied" in access_note:
                    erp.accessibilite.entree_plain_pied = True
                elif "rampe" in access_note:
                    erp.accessibilite.entree_plain_pied = False
                    erp.accessibilite.entree_marches_rampe = "fixe"
                else:
                    erp.accessibilite.commentaire = "Établissement accessible en fauteuil roulant"
            elif access == "NAC":
                erp.accessibilite.entree_plain_pied = False
            elif access == "DEM":
                erp.accessibilite.entree_plain_pied = False
                erp.accessibilite.entree_marches_rampe = "amovible"
                erp.accessibilite.entree_aide_humaine = True

        return erp, None
