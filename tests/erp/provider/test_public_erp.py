import json
import pytest

from django.contrib.gis.geos import Point

from erp.provider import public_erp
from erp.models import Activite, Commune

from tests.fixtures import (
    data,
    activite_administration_publique,
    activite_mairie,
    commune_castelnau,
    commune_montpellier,
    commune_montreuil,
)


def test_extract_numero_voie():
    cases = [
        ("", (None, "")),
        ("4 grand rue", ("4", "grand rue")),
        ("grand rue", (None, "grand rue")),
        ("4TER grand rue", ("4TER", "grand rue")),
    ]
    for case in cases:
        assert public_erp.extract_numero_voie(case[0]) == case[1]


def test_parse_feature_jacou(data, activite_mairie):
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
        "activite": activite_mairie.pk,
        "nom": "Mairie - Jacou",
        "siret": None,
        "numero": "4",
        "voie": "rue de l'Hôtel-de-Ville",
        "lieu_dit": None,
        "code_postal": data.jacou.code_postaux[0],
        "commune": data.jacou.nom,
        "code_insee": data.jacou.code_insee,
        "contact_email": "mairie@ville-jacou.fr",
        "telephone": "04 67 55 88 55",
        "site_internet": "http://www.ville-jacou.fr",
    }


def test_parse_feature_gendarmerie_castelnau(
    data, commune_castelnau, activite_administration_publique
):
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
    assert public_erp.parse_feature(json_feature) == {
        "source": "public_erp",
        "source_id": "gendarmerie-34057-01",
        "actif": True,
        "coordonnees": [3.91375272, 43.64536644],
        "naf": None,
        "activite": activite_administration_publique.pk,
        "nom": "Brigade de gendarmerie - Castelnau-le-Lez",
        "siret": None,
        "numero": "635",
        "voie": "Avenue de la Monnaie",
        "lieu_dit": None,
        "code_postal": commune_castelnau.code_postaux[0],
        "commune": commune_castelnau.nom,
        "code_insee": commune_castelnau.code_insee,
        "contact_email": None,
        "telephone": "04 99 74 29 50",
        "site_internet": "http://www.gendarmerie.interieur.gouv.fr",
    }


def test_parse_feature_montreuil(data, commune_montreuil, activite_mairie):
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
        "activite": activite_mairie.pk,
        "nom": "Mairie - Montreuil",
        "siret": None,
        "numero": "1",
        "voie": "place Aimé Césaire",
        "lieu_dit": "Centre administratif - Tour Altaïs",
        "code_postal": commune_montreuil.code_postaux[0],
        "commune": commune_montreuil.nom,
        "code_insee": commune_montreuil.code_insee,
        "contact_email": None,
        "telephone": "01 48 70 60 00",
        "site_internet": "http://www.montreuil.fr",
    }


def test_parse_prefecture_montpellier(
    data, commune_montpellier, activite_administration_publique
):
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
    assert public_erp.parse_feature(json_feature) == {
        "source": "public_erp",
        "source_id": "prefecture-34172-01",
        "actif": True,
        "coordonnees": [3.87658905983, 43.6109542847],
        "naf": None,
        "activite": activite_administration_publique.pk,
        "nom": "Préfecture de l'Hérault",
        "siret": None,
        "numero": "34",
        "voie": "place des Martyrs-de-la-Résistance",
        "lieu_dit": None,
        "code_postal": commune_montpellier.code_postaux[0],
        "commune": commune_montpellier.nom,
        "code_insee": commune_montpellier.code_insee,
        "contact_email": None,
        "telephone": "04 67 61 61 61",
        "site_internet": "http://www.herault.gouv.fr",
    }
