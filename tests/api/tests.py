import json
import uuid
from unittest.mock import ANY

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.usefixtures("api_client")
@pytest.mark.usefixtures("data")
class TestApi:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "url, status_code",
        [
            (reverse("openapi-schema"), 200),
            (reverse("apidocs"), 200),
            (reverse("api-root"), 200),
            (reverse("accessibilite-list"), 200),
            (reverse("accessibilite-help"), 200),
            (reverse("activite-list"), 200),
            (reverse("activite-list") + "?commune=Foo", 200),
            (reverse("erp-list"), 200),
        ],
    )
    def test_api_urls_ok(self, api_client, url, status_code):
        response = api_client.get(url)

        assert response.status_code == status_code


@pytest.mark.usefixtures("api_client")
@pytest.mark.usefixtures("data")
class TestErpApi:
    def test_list(self, api_client, data):
        response = api_client.get(reverse("erp-list"))

        content = json.loads(response.content)
        assert content["count"] == 1
        assert content["page_size"] == 20
        erp_json = content["results"][0]
        assert erp_json["nom"] == "Aux bons croissants"
        assert erp_json["activite"]["nom"] == "Boulangerie"
        assert erp_json["activite"]["slug"] == "boulangerie"
        assert erp_json["code_postal"] == "34830"
        assert "user" not in erp_json
        assert erp_json["accessibilite"]["accueil"]["accueil_visibilite"] is None
        assert erp_json["accessibilite"]["transport"]["transport_station_presence"] is None

        # same request with clean
        response = api_client.get(reverse("erp-list") + "?clean=true")
        content = json.loads(response.content)
        assert content["count"] == 1
        assert content["page_size"] == 20
        erp_json = content["results"][0]
        assert erp_json["nom"] == "Aux bons croissants"
        assert "transport" not in erp_json["accessibilite"]
        assert "accueil_visibilite" not in erp_json["accessibilite"]["accueil"]
        assert erp_json["accessibilite"]["accueil"]["sanitaires_presence"] is True
        assert erp_json["accessibilite"]["accueil"]["sanitaires_adaptes"] is False

        # same request with readable
        response = api_client.get(reverse("erp-list") + "?readable=true")
        content = json.loads(response.content)
        erp_json = content["results"][0]
        assert erp_json["accessibilite"]["datas"]["accueil"]["accueil_visibilite"] is None
        assert (
            erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_presence"]
            == "Des sanitaires sont mis à disposition dans l'établissement"
        )
        assert (
            erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_adaptes"]
            == "Aucun sanitaire adapté mis à disposition dans l'établissement"
        )
        assert erp_json["accessibilite"]["datas"]["transport"]["transport_station_presence"] is None

        # same request with readable & clean
        response = api_client.get(reverse("erp-list") + "?readable=true&clean=true")
        content = json.loads(response.content)
        erp_json = content["results"][0]
        assert "accueil_visibilite" not in erp_json["accessibilite"]["datas"]["accueil"]
        assert (
            erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_presence"]
            == "Des sanitaires sont mis à disposition dans l'établissement"
        )
        assert (
            erp_json["accessibilite"]["datas"]["accueil"]["sanitaires_adaptes"]
            == "Aucun sanitaire adapté mis à disposition dans l'établissement"
        )
        assert "transport" not in erp_json["accessibilite"]["datas"]

    def test_list_geojson(self, api_client, data):
        response = api_client.get(reverse("erp-list"), headers={"Content-Type": "application/geo+json"})
        assert response.json() == {
            "count": 1,
            "page_size": 20,
            "next": None,
            "previous": None,
            "results": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "id": 1,
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [3.9047933, 43.6648217]},
                        "properties": {
                            "nom": "Aux bons croissants",
                            "code_postal": "34830",
                            "voie": "grand rue",
                            "lieu_dit": None,
                            "commune": "Jacou",
                        },
                    }
                ],
            },
        }

    def test_list_page_size(self, api_client, data):
        response = api_client.get(reverse("erp-list") + "?page_size=25")
        content = json.loads(response.content)
        assert len(content["results"]) == 1
        assert content["page_size"] == 25

    def test_list_qs(self, api_client, data):
        response = api_client.get(reverse("erp-list") + "?q=croissants")
        content = json.loads(response.content)
        assert len(content["results"]) == 1

        response = api_client.get(reverse("erp-list") + "?q=nexiste_pas")
        content = json.loads(response.content)
        assert len(content["results"]) == 0

    def test_list_postal_code(self, api_client, data):
        # TODO: use several fixtures when we will have a real mechanism
        erp2 = data.erp
        erp2.pk = None
        erp2.uuid = uuid.uuid4()
        erp2.save()
        response = api_client.get(reverse("erp-list") + "?code_postal=34830")
        content = json.loads(response.content)
        assert len(content["results"]) == 2
        assert all([e["code_postal"] == "34830" for e in content["results"]])

        erp2.code_postal = 75010
        erp2.save()
        response = api_client.get(reverse("erp-list") + "?code_postal=34830")
        content = json.loads(response.content)
        assert len(content["results"]) == 1
        assert all([e["code_postal"] == "34830" for e in content["results"]])

    def test_list_asp_id(self, api_client, data):
        response = api_client.get(reverse("erp-list") + "?asp_id_not_null=true")
        content = json.loads(response.content)
        assert len(content["results"]) == 0

        response = api_client.get(reverse("erp-list") + "?asp_id_not_null=false")
        content = json.loads(response.content)
        assert len(content["results"]) == 1

    def test_detail(self, api_client, data):
        response = api_client.get(reverse("erp-detail", kwargs={"slug": data.erp.slug}))
        assert response.json() == {
            "url": "http://testserver/api/erps/aux-bons-croissants/",
            "web_url": "http://testserver/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/",
            "uuid": ANY,
            "activite": {"nom": "Boulangerie", "slug": "boulangerie"},
            "nom": "Aux bons croissants",
            "slug": "aux-bons-croissants",
            "adresse": "4 grand rue 34830 Jacou",
            "commune": "Jacou",
            "code_insee": ANY,
            "code_postal": "34830",
            "geom": {"type": "Point", "coordinates": [3.9047933, 43.6648217]},
            "siret": "52128577500016",
            "telephone": None,
            "site_internet": None,
            "contact_email": None,
            "contact_url": None,
            "user_type": "system",
            "accessibilite": {
                "url": f"http://testserver/api/accessibilite/{data.erp.accessibilite.id}/",
                "erp": "http://testserver/api/erps/aux-bons-croissants/",
                "transport": {
                    "transport_station_presence": None,
                    "transport_information": None,
                    "stationnement_presence": None,
                    "stationnement_pmr": None,
                    "stationnement_ext_presence": None,
                    "stationnement_ext_pmr": None,
                },
                "cheminement_ext": {
                    "cheminement_ext_presence": None,
                    "cheminement_ext_terrain_stable": None,
                    "cheminement_ext_plain_pied": None,
                    "cheminement_ext_ascenseur": None,
                    "cheminement_ext_nombre_marches": None,
                    "cheminement_ext_sens_marches": None,
                    "cheminement_ext_reperage_marches": None,
                    "cheminement_ext_main_courante": None,
                    "cheminement_ext_rampe": None,
                    "cheminement_ext_pente_presence": None,
                    "cheminement_ext_pente_degre_difficulte": None,
                    "cheminement_ext_pente_longueur": None,
                    "cheminement_ext_devers": None,
                    "cheminement_ext_bande_guidage": None,
                    "cheminement_ext_retrecissement": None,
                },
                "entree": {
                    "entree_reperage": True,
                    "entree_porte_presence": True,
                    "entree_porte_manoeuvre": None,
                    "entree_porte_type": None,
                    "entree_vitree": None,
                    "entree_vitree_vitrophanie": None,
                    "entree_plain_pied": None,
                    "entree_ascenseur": None,
                    "entree_marches": None,
                    "entree_marches_sens": None,
                    "entree_marches_reperage": None,
                    "entree_marches_main_courante": None,
                    "entree_marches_rampe": None,
                    "entree_dispositif_appel": None,
                    "entree_dispositif_appel_type": [],
                    "entree_balise_sonore": None,
                    "entree_aide_humaine": None,
                    "entree_largeur_mini": None,
                    "entree_pmr": None,
                    "entree_pmr_informations": None,
                },
                "accueil": {
                    "accueil_visibilite": None,
                    "accueil_cheminement_plain_pied": None,
                    "accueil_cheminement_ascenseur": None,
                    "accueil_cheminement_nombre_marches": None,
                    "accueil_cheminement_sens_marches": None,
                    "accueil_cheminement_reperage_marches": None,
                    "accueil_cheminement_main_courante": None,
                    "accueil_cheminement_rampe": None,
                    "accueil_retrecissement": None,
                    "accueil_chambre_nombre_accessibles": None,
                    "accueil_chambre_douche_plain_pied": None,
                    "accueil_chambre_douche_siege": None,
                    "accueil_chambre_douche_barre_appui": None,
                    "accueil_chambre_sanitaires_barre_appui": None,
                    "accueil_chambre_sanitaires_espace_usage": None,
                    "accueil_chambre_numero_visible": None,
                    "accueil_chambre_equipement_alerte": None,
                    "accueil_chambre_accompagnement": None,
                    "accueil_personnels": None,
                    "accueil_audiodescription_presence": None,
                    "accueil_audiodescription": [],
                    "accueil_equipements_malentendants_presence": None,
                    "accueil_equipements_malentendants": [],
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": False,
                },
                "registre": {"registre_url": None},
                "conformite": {"conformite": None},
                "commentaire": {
                    "labels": [],
                    "labels_familles_handicap": [],
                    "labels_autre": None,
                    "commentaire": "foo",
                },
            },
            "distance": None,
            "source_id": None,
            "asp_id": None,
        }


@pytest.mark.usefixtures("api_client")
@pytest.mark.usefixtures("data")
class TestActiviteApi:
    def test_get(self, api_client, data):
        response = api_client.get(reverse("activite-list"))
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"nom": "Boulangerie", "slug": "boulangerie", "count": 1}],
        }


@pytest.mark.usefixtures("api_client")
@pytest.mark.usefixtures("data")
class TestAccessibiliteApi:
    def test_get(self, api_client, data):
        response = api_client.get(reverse("accessibilite-list"))
        assert response.json() == {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "url": f"http://testserver/api/accessibilite/{data.erp.accessibilite.id}/",
                    "erp": "http://testserver/api/erps/aux-bons-croissants/",
                    "transport": {
                        "transport_station_presence": None,
                        "transport_information": None,
                        "stationnement_presence": None,
                        "stationnement_pmr": None,
                        "stationnement_ext_presence": None,
                        "stationnement_ext_pmr": None,
                    },
                    "cheminement_ext": {
                        "cheminement_ext_presence": None,
                        "cheminement_ext_terrain_stable": None,
                        "cheminement_ext_plain_pied": None,
                        "cheminement_ext_ascenseur": None,
                        "cheminement_ext_nombre_marches": None,
                        "cheminement_ext_sens_marches": None,
                        "cheminement_ext_reperage_marches": None,
                        "cheminement_ext_main_courante": None,
                        "cheminement_ext_rampe": None,
                        "cheminement_ext_pente_presence": None,
                        "cheminement_ext_pente_degre_difficulte": None,
                        "cheminement_ext_pente_longueur": None,
                        "cheminement_ext_devers": None,
                        "cheminement_ext_bande_guidage": None,
                        "cheminement_ext_retrecissement": None,
                    },
                    "entree": {
                        "entree_reperage": True,
                        "entree_porte_presence": True,
                        "entree_porte_manoeuvre": None,
                        "entree_porte_type": None,
                        "entree_vitree": None,
                        "entree_vitree_vitrophanie": None,
                        "entree_plain_pied": None,
                        "entree_ascenseur": None,
                        "entree_marches": None,
                        "entree_marches_sens": None,
                        "entree_marches_reperage": None,
                        "entree_marches_main_courante": None,
                        "entree_marches_rampe": None,
                        "entree_dispositif_appel": None,
                        "entree_dispositif_appel_type": [],
                        "entree_balise_sonore": None,
                        "entree_aide_humaine": None,
                        "entree_largeur_mini": None,
                        "entree_pmr": None,
                        "entree_pmr_informations": None,
                    },
                    "accueil": {
                        "accueil_visibilite": None,
                        "accueil_cheminement_plain_pied": None,
                        "accueil_cheminement_ascenseur": None,
                        "accueil_cheminement_nombre_marches": None,
                        "accueil_cheminement_sens_marches": None,
                        "accueil_cheminement_reperage_marches": None,
                        "accueil_cheminement_main_courante": None,
                        "accueil_cheminement_rampe": None,
                        "accueil_retrecissement": None,
                        "accueil_chambre_nombre_accessibles": None,
                        "accueil_chambre_douche_plain_pied": None,
                        "accueil_chambre_douche_siege": None,
                        "accueil_chambre_douche_barre_appui": None,
                        "accueil_chambre_sanitaires_barre_appui": None,
                        "accueil_chambre_sanitaires_espace_usage": None,
                        "accueil_chambre_numero_visible": None,
                        "accueil_chambre_equipement_alerte": None,
                        "accueil_chambre_accompagnement": None,
                        "accueil_personnels": None,
                        "accueil_audiodescription_presence": None,
                        "accueil_audiodescription": [],
                        "accueil_equipements_malentendants_presence": None,
                        "accueil_equipements_malentendants": [],
                        "sanitaires_presence": True,
                        "sanitaires_adaptes": False,
                    },
                    "registre": {"registre_url": None},
                    "conformite": {"conformite": None},
                    "commentaire": {
                        "labels": [],
                        "labels_familles_handicap": [],
                        "labels_autre": None,
                        "commentaire": "foo",
                    },
                }
            ],
        }
