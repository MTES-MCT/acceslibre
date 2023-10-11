import copy
import json

import pytest
from django.contrib.gis.geos import Point

from erp.imports.fetcher import Fetcher
from erp.models import Commune


@pytest.fixture
def neufchateau(db):
    return Commune.objects.create(
        nom="Neufchâteau",
        slug="88-neufchateau",
        departement="88",
        code_insee="88321",
        superficie=2380,
        population=6639,
        geom=Point(5.6962, 48.3568),
        code_postaux=["88300"],
    )


@pytest.fixture
def jacou():
    return Commune.objects.create(
        nom="Jacou",
        slug="34-jacou",
        code_postaux=["34830"],
        code_insee="34830",
        departement="34",
        superficie=2380,
        population=6639,
        geom=Point(5.6962, 48.3568),
    )


@pytest.fixture
def paris():
    return Commune.objects.create(
        nom="Paris",
        slug="75-paris",
        code_postaux=["75002"],
        code_insee="75111",
        departement="75",
        superficie=2380,
        population=6639,
        geom=Point(5.6962, 48.3568),
    )


@pytest.fixture
def vallorcine(db):
    return Commune.objects.create(
        nom="Vallorcine",
        slug="74-vallorcine",
        departement="74",
        code_insee="74660",
        superficie=2380,
        population=6639,
        geom=Point(6.93822479248, 46.0415725708),
        code_postaux=["74660"],
    )


@pytest.fixture
def sample_record_ok():
    return json.loads(
        """
{
    "type": "Feature",
    "properties": {
        "gid": 152,
        "c_gid": 219,
        "c_nom": "Centre de vaccination de Neufchateau",
        "c_xy_precis": "0.99999984569228",
        "c_id_adr": "88321_0105_01281",
        "c_adr_num": "1280",
        "c_adr_voie": "Avenue de la Division Leclerc",
        "c_com_cp": "88300",
        "c_com_insee": "88321",
        "c_com_nom": "Neufch\u00e2teau",
        "c_lat_coor1": 48.3704,
        "c_long_coor1": 5.7077,
        "c_structure_siren": "130007834",
        "c_structure_type": "8412Z",
        "c_structure_rais": "AGENCE REGIONALE DE SANTE GRAND EST",
        "c_structure_num": "3",
        "c_structure_voie": "BD JOFFRE",
        "c_structure_cp": "54000",
        "c_structure_insee": "54395",
        "c_structure_com": "NANCY",
        "c__edit_datemaj": "2021/02/04 16:21:11.620",
        "c_lieu_accessibilite": null,
        "c_rdv_lundi": "14:00-18:00",
        "c_rdv_mardi": "14:00-18:00",
        "c_rdv_mercredi": "14:00-18:00",
        "c_rdv_jeudi": "14:00-18:00",
        "c_rdv_vendredi": "14:00-18:00",
        "c_rdv_samedi": "14:00-18:00",
        "c_rdv_dimanche": "ferm\u00e9",
        "c_rdv": true,
        "c_date_fermeture": null,
        "c_date_ouverture": "2021-01-08",
        "c_rdv_site_web": "https://partners.doctolib.fr/hopital-public/neufchateau/centre-de-vaccination-covid-neufchateau-et-vittel?speciality_id=5494\u0026enable_cookies_consent=1",
        "c_rdv_tel": "+33329948605",
        "c_rdv_modalites": null,
        "c_rdv_consultation_prevaccination": true
    },
    "geometry": {
        "type": "MultiPoint",
        "coordinates": [[5.7076970492316, 48.370392643203]]
    }
}"""
    )


@pytest.fixture
def record_skippable(sample_record_ok):
    record_to_skip = copy.deepcopy(sample_record_ok)
    record_to_skip["properties"]["c_gid"] = 100
    record_to_skip["properties"]["c_rdv_modalites"] = "Établissement Pénitentiaire"
    return record_to_skip


@pytest.fixture
def record_invalid_cp(sample_record_ok):
    record_throwing_error = copy.deepcopy(sample_record_ok)
    record_throwing_error["properties"]["c_gid"] = 200
    record_throwing_error["properties"]["c_com_insee"] = "97801"
    record_throwing_error["properties"]["c_com_cp"] = "97150"
    return record_throwing_error


@pytest.fixture
def service_public_valid(db):
    return {
        "plage_ouverture": [
            {
                "nom_jour_debut": "Mardi",
                "nom_jour_fin": "Mardi",
                "valeur_heure_debut_1": "09:00:00",
                "valeur_heure_fin_1": "12:00:00",
                "valeur_heure_debut_2": "18:00:00",
                "valeur_heure_fin_2": "19:00:00",
                "commentaire": "Accueil ouvert uniquement hors vacances scolaires l'après-midi.",
            },
            {
                "nom_jour_debut": "Mercredi",
                "nom_jour_fin": "Mercredi",
                "valeur_heure_debut_1": "09:00:00",
                "valeur_heure_fin_1": "12:00:00",
                "valeur_heure_debut_2": "",
                "valeur_heure_fin_2": "",
                "commentaire": "",
            },
            {
                "nom_jour_debut": "Vendredi",
                "nom_jour_fin": "Vendredi",
                "valeur_heure_debut_1": "09:00:00",
                "valeur_heure_fin_1": "12:00:00",
                "valeur_heure_debut_2": "",
                "valeur_heure_fin_2": "",
                "commentaire": "",
            },
        ],
        "site_internet": [{"libelle": "", "valeur": "http://www.ville-fontaineleport.fr"}],
        "copyright": "Direction de l'information légale et administrative (Première ministre)",
        "siren": "",
        "ancien_code_pivot": "mairie-77188-01",
        "reseau_social": [],
        "texte_reference": [],
        "partenaire": "",
        "telecopie": ["01 64 38 36 07"],
        "nom": "Mairie - Fontaine-le-Port",
        "siret": "21770188700010",
        "itm_identifiant": "389008",
        "sigle": "",
        "affectation_personne": [],
        "date_modification": "09/08/2023 13:30:19",
        "adresse_courriel": ["mairie-xxxxx@yyyy.fr"],
        "service_disponible": "",
        "organigramme": [],
        "pivot": [{"type_service_local": "mairie", "code_insee_commune": ["77188"]}],
        "partenaire_identifiant": "",
        "ancien_identifiant": [],
        "id": "00007e4d-264c-43a0-b0b7-7f3b7dd995ab",
        "ancien_nom": [],
        "commentaire_plage_ouverture": "",
        "annuaire": [],
        "tchat": [],
        "hierarchie": [],
        "categorie": "SL",
        "sve": [],
        "telephone_accessible": [],
        "application_mobile": [],
        "version_type": "Publiable",
        "type_repertoire": "",
        "telephone": [{"valeur": "01 64 38 30 52", "description": ""}],
        "version_etat_modification": "",
        "date_creation": "18/01/2012 00:00:00",
        "partenaire_date_modification": "",
        "mission": "",
        "formulaire_contact": [],
        "version_source": "",
        "type_organisme": "",
        "code_insee_commune": "77188",
        "statut_de_diffusion": "true",
        "adresse": [
            {
                "type_adresse": "Adresse",
                "complement1": "",
                "complement2": "",
                "numero_voie": "3 rue du Général-Roux",
                "service_distribution": "",
                "code_postal": "77590",
                "nom_commune": "Fontaine-le-Port",
                "pays": "",
                "continent": "",
                "longitude": "2.75745010376",
                "latitude": "48.4868011475",
                "accessibilite": "DEM",
                "note_accessibilite": "",
            }
        ],
        "url_service_public": "https://lannuaire.service-public.fr/ile-de-france/seine-et-marne/00007e4d-264c-43a0-b0b7-7f3b7dd995ab",
        "information_complementaire": "",
        "date_diffusion": "",
    }


@pytest.fixture
def gendarmeries_valid(db):
    Commune.objects.create(
        nom="Oyonnax",
        slug=" 01 - oyonnax",
        departement="01",
        code_insee="01283",
        superficie=3626,
        population=22559,
        geom=Point(5.6962, 48.3568),
        code_postaux=["01100"],
    )
    Commune.objects.create(
        nom="Ornex",
        slug="01-ornex",
        departement="01",
        code_insee="01281",
        superficie=569,
        population=4400,
        geom=Point(5.6962, 48.3568),
        code_postaux=["01210"],
    )
    Commune.objects.create(
        nom="Belley",
        slug="01 - belley",
        departement="01",
        code_insee="01034",
        superficie=2251,
        population=9133,
        geom=Point(5.6962, 48.3568),
        code_postaux=["01300"],
    )
    return [
        {
            "identifiant_public_unite": "1008620",
            "service": "Gendarmerie - Brigade d'Ornex",
            "adresse_geographique": "124 Rue de Béjoud 01210 ORNEX",
            "telephone": "+33 4 50 40 59 30",
            "departement": "01",
            "code_commune_insee": "01281",
            "voie": "124 Rue de Béjoud",
            "code_postal": "01210",
            "commune": "Ornex",
            "geocodage_epsg": "",
            "geocodage_x": "",
            "geocodage_y": "",
            "geocodage_x_GPS": "6.09523",
            "geocodage_y_GPS": "46.27591",
            "horaires_accueil": " Lundi : 8h00-12h00 14h00-18h00 Mardi : 8h00-12h00 14h00-18h00 Mercredi : 14h00-18h00 Jeudi : 8h00-12h00 14h00-18h00 Vendredi : 8h00-12h00 14h00-18h00 Samedi : 14h00-18h00 Dimanche : 9h00-12h00 15h00-18h00",
            "url": "https://lannuaire.service-public.fr/auvergne-rhone-alpes/ain/gendarmerie-01281-01",
        },
        {
            "identifiant_public_unite": "1008614",
            "service": "Gendarmerie - Brigade d'Oyonnax",
            "adresse_geographique": "144 Rue Sainte-Geneviève 01100 OYONNAX",
            "telephone": "+33 4 74 77 16 33",
            "departement": "01",
            "code_commune_insee": "01283",
            "voie": "144 Rue Sainte-Geneviève",
            "code_postal": "01100",
            "commune": "Oyonnax",
            "geocodage_epsg": "",
            "geocodage_x": "",
            "geocodage_y": "",
            "geocodage_x_GPS": "5.64149",
            "geocodage_y_GPS": "46.25539",
            "horaires_accueil": "",
            "url": "https://lannuaire.service-public.fr/auvergne-rhone-alpes/ain/gendarmerie-01283-01",
        },
        {
            "identifiant_public_unite": "1008593",
            "service": "Gendarmerie - Brigade de Belley",
            "adresse_geographique": "Caserne Sibuet 9 Rue Mante 01300 BELLEY",
            "telephone": "+33 4 79 81 69 00",
            "departement": "01",
            "code_commune_insee": "01034",
            "voie": "Caserne Sibuet 9 Rue Mante",
            "code_postal": "01300",
            "commune": "Belley",
            "geocodage_epsg": "",
            "geocodage_x": "",
            "geocodage_y": "",
            "geocodage_x_GPS": "5.68275",
            "geocodage_y_GPS": "45.75554",
            "horaires_accueil": "",
            "url": "https://lannuaire.service-public.fr/auvergne-rhone-alpes/ain/gendarmerie-01034-01",
        },
    ]


class FakeJsonFetcher(Fetcher):
    def __init__(self, content):
        self.content = content

    def fetch(self, url=None):
        return self.content
