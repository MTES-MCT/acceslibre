import json
import pytest

from erp import public_erp

from tests.fixtures import data


def test_extract_numero_voie():
    cases = [
        ("", (None, "")),
        ("4 grand rue", ("4", "grand rue")),
        ("grand rue", (None, "grand rue")),
        ("4TER grand rue", ("4TER", "grand rue")),
    ]
    for case in cases:
        assert public_erp.extract_numero_voie(case[0]) == case[1]


def test_parse_feature_jacou(data):
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
    assert public_erp.parse_feature(json_feature) == {
        "source": "public_erp",
        "source_id": "mairie-34120-01",
        "actif": True,
        "coordonnees": [3.9106014, 43.6609939],
        "naf": None,
        "activite": data.mairie.pk,
        "nom": "Mairie - Jacou",
        "siret": None,
        "numero": "4",
        "voie": "rue de l'Hôtel-de-Ville",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "34120",
        "contact_email": "mairie@ville-jacou.fr",
        "telephone": "04 67 55 88 55",
        "site_internet": "http://www.ville-jacou.fr",
    }


def test_parse_feature_gendarmerie(data):
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
                "url":"http://www.gendarmerie.interieur.gouv.fr",
                "zonage":{
                    "communes":[
                        "34169 Montferrier-sur-Lez",
                        "34057 Castelnau-le-Lez",
                        "34120 Jacou",
                        "34077 Clapiers"
                    ]
                }
            }
        }"""
    )
    assert public_erp.parse_feature(json_feature) == {
        "source": "public_erp",
        "source_id": "gendarmerie-34057-01",
        "actif": True,
        "coordonnees": [3.91375272, 43.64536644],
        "naf": None,
        "activite": data.administration_publique.pk,
        "nom": "Brigade de gendarmerie - Castelnau-le-Lez",
        "siret": None,
        "numero": "635",
        "voie": "Avenue de la Monnaie",
        "lieu_dit": None,
        "code_postal": "34170",
        "commune": "Castelnau-le-Lez",
        "code_insee": "34057",
        "contact_email": None,
        "telephone": "04 99 74 29 50",
        "site_internet": "http://www.gendarmerie.interieur.gouv.fr",
    }


def test_parse_feature_montreuil(data):
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
    assert public_erp.parse_feature(json_feature) == {
        "source": "public_erp",
        "source_id": "mairie-93048-01",
        "actif": True,
        "coordonnees": [2.441878, 48.860395],
        "naf": None,
        "activite": data.mairie.pk,
        "nom": "Mairie - Montreuil",
        "siret": None,
        "numero": "1",
        "voie": "place Aimé Césaire",
        "lieu_dit": "Centre administratif - Tour Altaïs",
        "code_postal": "93100",
        "commune": "Montreuil",
        "code_insee": "93048",
        "contact_email": None,
        "telephone": "01 48 70 60 00",
        "site_internet": "http://www.montreuil.fr",
    }
