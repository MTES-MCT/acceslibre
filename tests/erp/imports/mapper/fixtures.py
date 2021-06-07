import json
import pytest

from django.contrib.gis.geos import Point

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
