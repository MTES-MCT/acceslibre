import json

import pytest

from erp.provider import public_erp
from tests.factories import ActiviteFactory, CommuneFactory


def test_find_public_types_simple():
    assert public_erp.find_public_types("dlfhsdjhfsjh") == []
    assert public_erp.find_public_types("Commissariat de police")[0] == "commissariat_police"
    assert public_erp.find_public_types("commissariat")[0] == "commissariat_police"
    assert public_erp.find_public_types("maison du handicap")[0] == "maison_handicapees"
    assert public_erp.find_public_types("MDPH hérault")[0] == "maison_handicapees"
    assert public_erp.find_public_types("protection enfant")[0] == "pmi"
    assert public_erp.find_public_types("ASSEDIC castelnau le lez")[0] == "pole_emploi"
    assert public_erp.find_public_types("préfécture à paris")[0] == "prefecture"
    assert public_erp.find_public_types("sous prefecture")[0] == "sous_pref"
    assert public_erp.find_public_types("accompagnement gériatrie")[0] == "accompagnement_personnes_agees"

    assert public_erp.find_public_types("information logement")[0] == "adil"
    assert public_erp.find_public_types("formation pro")[0] == "afpa"
    assert public_erp.find_public_types("ARS rhone")[0] == "ars_antenne"
    assert public_erp.find_public_types("aide aux victimes")[0] == "bav"
    assert public_erp.find_public_types("service civique")[0] == "bsn"
    assert public_erp.find_public_types("cour d'appel")[0] == "cour_appel"
    assert public_erp.find_public_types("cci montpellier")[0] == "cci"
    assert public_erp.find_public_types("droits des femmes")[0] == "cidf"


def test_find_public_types_multiple():
    prisons = public_erp.find_public_types("prison de fresnes")
    assert "centre_penitentiaire" in prisons
    assert "centre_detention" in prisons
    assert "maison_arret" in prisons

    impots = public_erp.find_public_types("impots")
    assert "centre_impots_fonciers" in impots
    assert "sie" in impots
    assert "sip" in impots
    assert "urssaf" in impots

    tribunaux = public_erp.find_public_types("tribunal")
    assert "ta" in tribunaux
    assert "te" in tribunaux
    assert "tgi" in tribunaux
    assert "ti" in tribunaux
    assert "tribunal_commerce" in tribunaux


def test_extract_numero_voie():
    cases = [
        ("", (None, "")),
        ("4 grand rue", ("4", "grand rue")),
        ("grand rue", (None, "grand rue")),
        ("4TER grand rue", ("4TER", "grand rue")),
    ]
    for case in cases:
        assert public_erp.extract_numero_voie(case[0]) == case[1]


@pytest.mark.django_db
def test_parse_etablissement_jacou():
    mairie = ActiviteFactory(nom="Mairie")
    commune = CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
    json_feature = json.loads(
        """
        {
            "type": "Feature",
            "geometry": { "type": "Point", "coordinates": [3.9106014, 43.6609939] },
            "properties": {
                "id": "mairie-34120-01",
                "codeInsee": "34120",
                "pivotLocal": "mairie",
                "nom": "Mairie - Jacou",
                "adresses": [
                    {
                        "type": "géopostale",
                        "lignes": ["4 rue de l'Hôtel-de-Ville"],
                        "codePostal": "34830",
                        "commune": "Jacou",
                        "coordonnees": [3.9106014, 43.6609939]
                    }
                ],
                "email": "mairie@ville-jacou.fr",
                "telephone": "04 67 55 88 55",
                "url": "http://www.ville-jacou.fr",
                "zonage": { "communes": ["34120 Jacou"] }
            }
        }"""
    )
    assert public_erp.parse_etablissement(json_feature, mairie, None) == {
        "source": "public_erp",
        "source_id": "mairie-34120-01",
        "coordonnees": [3.9106014, 43.6609939],
        "naf": None,
        "activite": mairie.pk,
        "nom": "Mairie - Jacou",
        "siret": None,
        "numero": "4",
        "voie": "rue de l'Hôtel-de-Ville",
        "lieu_dit": None,
        "code_postal": commune.code_postaux[0],
        "commune": commune.nom,
        "code_insee": commune.code_insee,
        "contact_email": "mairie@ville-jacou.fr",
        "telephone": "04 67 55 88 55",
        "site_internet": "http://www.ville-jacou.fr",
    }


@pytest.mark.django_db
def test_parse_etablissement_gendarmerie_castelnau():
    commune = CommuneFactory(nom="Castelnau-le-Lez", code_postaux=["34170"], code_insee="34057", departement="93")
    public_admin = ActiviteFactory(nom="Administration Publique")

    json_feature = json.loads(
        """
        {
            "type":"Feature",
            "geometry":{
                "type":"Point",
                "coordinates":[
                    3.91375272,
                    43.64536644
                ]
            },
            "properties":{
                "id":"gendarmerie-34057-01",
                "codeInsee":"34057",
                "pivotLocal":"gendarmerie",
                "nom":"Brigade de gendarmerie - Castelnau-le-Lez",
                "adresses":[
                    {
                        "type":"géopostale",
                        "lignes":[
                            "635 Avenue de la Monnaie"
                        ],
                        "codePostal":"34170",
                        "commune":"Castelnau-le-Lez",
                        "coordonnees":[
                            3.91375272,
                            43.64536644
                        ]
                    }
                ],
                "email":"https://www.contacterlagendarmerie.fr",
                "telephone":"04 99 74 29 50",
                "url":"http://www.gendarmerie.interieur.gouv.fr"
            }
        }"""
    )
    assert public_erp.parse_etablissement(json_feature, None, public_admin) == {
        "source": "public_erp",
        "source_id": "gendarmerie-34057-01",
        "coordonnees": [3.91375272, 43.64536644],
        "naf": None,
        "activite": public_admin.pk,
        "nom": "Brigade de gendarmerie - Castelnau-le-Lez",
        "siret": None,
        "numero": "635",
        "voie": "Avenue de la Monnaie",
        "lieu_dit": None,
        "code_postal": commune.code_postaux[0],
        "commune": commune.nom,
        "code_insee": commune.code_insee,
        "contact_email": None,
        "telephone": "04 99 74 29 50",
        "site_internet": "http://www.gendarmerie.interieur.gouv.fr",
    }


@pytest.mark.django_db
def test_parse_etablissement_montreuil():
    commune = CommuneFactory(nom="Montreuil", code_postaux=["93100"], code_insee="93048", departement="93")

    mairie = ActiviteFactory(nom="Mairie")

    json_feature = json.loads(
        """
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [2.441878, 48.860395]
            },
            "properties": {
                "id": "mairie-93048-01",
                "codeInsee": "93048",
                "pivotLocal": "mairie",
                "nom": "Mairie - Montreuil",
                "adresses": [
                    {
                        "type": "physique",
                        "lignes": [
                            "1 place Aimé Césaire",
                            "Centre administratif - Tour Altaïs"
                        ],
                        "codePostal": "93100",
                        "commune": "Montreuil",
                        "coordonnees": [2.441878, 48.860395]
                    },
                    {
                        "type": "postale",
                        "lignes": ["Place Jean-Jaurès"],
                        "codePostal": "93105",
                        "commune": "Montreuil Cedex"
                    }
                ],
                "email": "http://www.montreuil.fr/outils/contactez-nous",
                "telephone": "01 48 70 60 00",
                "url": "http://www.montreuil.fr",
                "zonage": { "communes": ["93048 Montreuil"] }
            }
        }"""
    )
    assert public_erp.parse_etablissement(json_feature, mairie, None) == {
        "source": "public_erp",
        "source_id": "mairie-93048-01",
        "coordonnees": [2.441878, 48.860395],
        "naf": None,
        "activite": mairie.pk,
        "nom": "Mairie - Montreuil",
        "siret": None,
        "numero": "1",
        "voie": "place Aimé Césaire",
        "lieu_dit": "Centre administratif - Tour Altaïs",
        "code_postal": commune.code_postaux[0],
        "commune": commune.nom,
        "code_insee": commune.code_insee,
        "contact_email": None,
        "telephone": "01 48 70 60 00",
        "site_internet": "http://www.montreuil.fr",
    }


@pytest.mark.django_db
def test_parse_prefecture_montpellier():
    commune = CommuneFactory(nom="Montpellier", code_postaux=["34000"], code_insee="34172", departement="34")
    public_admin = ActiviteFactory(nom="Administration Publique")

    json_feature = json.loads(
        """
        {
            "type": "Feature",
            "geometry":{
                "type": "Point",
                "coordinates":[
                    3.87658905983,
                    43.6109542847
                ]
            },
            "properties":{
                "id": "prefecture-34172-01",
                "codeInsee": "34172",
                "pivotLocal": "prefecture",
                "nom": "Préfecture de l'Hérault",
                "adresses":[
                    {
                        "type": "géopostale",
                        "lignes":[
                            "34, place des Martyrs-de-la-Résistance"
                        ],
                        "codePostal": "34062",
                        "commune": "Montpellier Cedex 2",
                        "coordonnees":[
                            3.87658905983,
                            43.6109542847
                        ]
                    }
                ],
                "telephone": "04 67 61 61 61",
                "url": "http://www.herault.gouv.fr"
            }
        }"""
    )
    assert public_erp.parse_etablissement(json_feature, None, public_admin) == {
        "source": "public_erp",
        "source_id": "prefecture-34172-01",
        "coordonnees": [3.87658905983, 43.6109542847],
        "naf": None,
        "activite": public_admin.pk,
        "nom": "Préfecture de l'Hérault",
        "siret": None,
        "numero": "34",
        "voie": "place des Martyrs-de-la-Résistance",
        "lieu_dit": None,
        "code_postal": "34062",
        "commune": commune.nom,
        "code_insee": commune.code_insee,
        "contact_email": None,
        "telephone": "04 67 61 61 61",
        "site_internet": "http://www.herault.gouv.fr",
    }
