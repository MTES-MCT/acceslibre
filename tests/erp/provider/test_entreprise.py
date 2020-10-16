import json
import pytest

from django.contrib.gis.geos import Point

from erp.provider import entreprise
from erp.models import Activite, Commune

from tests.fixtures import (
    data,
    #     activite_administration_publique,
    #     activite_mairie,
    #     commune_castelnau,
    #     commune_montpellier,
    #     commune_montreuil,
)


def test_parse_etablissement_jacou(data):
    json_feature = json.loads(
        """
        {
            "id": 63015890,
            "siret": "88076068100010",
            "l1_normalisee": "AKEI",
            "numero_voie": "4",
            "indice_repetition": null,
            "type_voie": null,
            "libelle_voie": "GRAND RUE",
            "code_postal": "34830",
            "departement": "34",
            "libelle_commune": "Jacou",
            "enseigne": null,
            "activite_principale": "6202A",
            "nom_raison_sociale": "AKEI",
            "departement_commune_siege": "34120",
            "email": null,
            "activite_principale_entreprise": "6202A",
            "longitude": "3.913557",
            "latitude": "43.657028",
            "geo_adresse": "4 Grand Rue 34830 Jacou"
        }"""
    )
    assert entreprise.parse_etablissement(json_feature) == {
        "source": "entreprise_api",
        "source_id": "63015890",
        "actif": True,
        "coordonnees": [3.913557, 43.657028],
        "naf": "62.02A",
        "activite": None,
        "nom": "AKEI",
        "siret": "88076068100010",
        "numero": "4",
        "voie": "GRAND RUE",
        "lieu_dit": None,
        "code_postal": "34830",
        "commune": "Jacou",
        "code_insee": "34120",
        "contact_email": None,
        "telephone": None,
        "site_internet": None,
    }
