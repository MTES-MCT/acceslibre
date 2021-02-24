import json
import pytest

from django.contrib.gis.geos import Point

from erp.models import Commune


@pytest.fixture
def neufchateau(db):
    return Commune.objects.create(
        **{
            "nom": "Neufchâteau",
            "slug": "88-neufchateau",
            "departement": "88",
            "code_insee": "88321",
            "superficie": 2380,
            "population": 6639,
            "geom": Point(5.6962, 48.3568),
            "code_postaux": ["88300"],
        }
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
        "c_rdv_consultation_prevaccination": null
    },
    "geometry": {
        "type": "MultiPoint",
        "coordinates": [[5.7076970492316, 48.370392643203]]
    }
}"""
    )


@pytest.fixture
def sample_record_reserve_ps():
    return json.loads(
        """
{
    "type": "Feature",
    "properties": {
        "gid": 169,
        "c_gid": 238,
        "c_nom": "CH Mas Careiron",
        "c_xy_precis": "0.999999564363",
        "c_id_adr": "30334_0270_00016_bis",
        "c_adr_num": "16 bis",
        "c_adr_voie": "Chemin du Paradis",
        "c_com_cp": "30700",
        "c_com_insee": "30334",
        "c_com_nom": "Uz\u00e8s",
        "c_lat_coor1": 44.0083,
        "c_long_coor1": 4.41307,
        "c_structure_siren": "130008048",
        "c_structure_type": "8412Z",
        "c_structure_rais": "AGENCE REGIONALE DE SANTE OCCITANIE",
        "c_structure_num": "1025",
        "c_structure_voie": "AV HENRI BECQUEREL",
        "c_structure_cp": "34000",
        "c_structure_insee": "34172",
        "c_structure_com": "MONTPELLIER",
        "c__edit_datemaj": "2021/02/04 12:07:14.218",
        "c_lieu_accessibilite": null,
        "c_rdv_lundi": "ferm\u00e9",
        "c_rdv_mardi": "ferm\u00e9",
        "c_rdv_mercredi": "9:00-16:30",
        "c_rdv_jeudi": "ferm\u00e9",
        "c_rdv_vendredi": "9:00-16:30",
        "c_rdv_samedi": "ferm\u00e9",
        "c_rdv_dimanche": "ferm\u00e9",
        "c_rdv": true,
        "c_date_fermeture": "2021-02-01",
        "c_date_ouverture": "2021-01-13",
        "c_rdv_site_web": "https://partners.doctolib.fr/hopital-public/uzes/centre-de-vaccination-covid-ch-le-mas-careiron?pid=practice-164184\u0026enable_cookies_consent=1",
        "c_rdv_tel": "+33809541919",
        "c_rdv_modalites": null,
        "c_rdv_consultation_prevaccination": null
    },
    "geometry": {
        "type": "MultiPoint",
        "coordinates": [[4.4130655367765, 44.008294265819]]
    }
}"""
    )
