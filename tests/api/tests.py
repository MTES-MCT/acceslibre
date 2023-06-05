import json
import uuid
from unittest.mock import ANY

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from erp.models import Erp


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
        geojson_expected_for_erp = {
            "type": "FeatureCollection",
            "count": 1,
            "next": None,
            "previous": None,
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [3.9047933, 43.6648217]},
                    "properties": {
                        "uuid": str(data.erp.uuid),
                        "nom": "Aux bons croissants",
                        "adresse": "4 grand rue 34830 Jacou",
                        "activite": {"nom": "Boulangerie", "vector_icon": "building"},
                        "web_url": "http://testserver/app/34-jacou/a/boulangerie/erp/aux-bons-croissants/",
                    },
                }
            ],
        }
        geojson_expected_for_no_results = {
            "type": "FeatureCollection",
            "count": 0,
            "next": None,
            "previous": None,
            "features": [],
        }

        response = api_client.get(
            reverse("erp-list") + "?zone=3.897168,43.653841,3.929097,43.676100",
            headers={"Accept": "application/geo+json"},
        )
        assert response.json() == geojson_expected_for_erp
        # bbox without results
        response = api_client.get(reverse("erp-list") + "?zone=4,44,5,45", headers={"Accept": "application/geo+json"})
        assert response.json() == geojson_expected_for_no_results

        # combination of bbox + filter
        response = api_client.get(
            reverse("erp-list") + "?zone=3.897168,43.653841,3.929097,43.676100&code_postal=34830",
            headers={"Accept": "application/geo+json"},
        )
        assert response.json() == geojson_expected_for_erp

        response = api_client.get(
            reverse("erp-list") + "?zone=3.897168,43.653841,3.929097,43.676100&code_postal=26000",
            headers={"Accept": "application/geo+json"},
        )
        assert response.json() == geojson_expected_for_no_results

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
            "created_at": ANY,
            "updated_at": ANY,
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

    def test_post(self, api_client, activite, commune_montreuil):
        assert not Erp.objects.filter(nom="Mairie de Montreuil").first()
        payload = {
            "activite": "Mairie",
            "nom": "Mairie de Montreuil",
            "numero": "101",
            "voie": "rue Francis de Pressencé",
            "commune": "Montreuil",
            "code_insee": "69100",
            "code_postal": "69100",
            "site_internet": "https://example.com",
            "contact_email": "user@example.com",
            "contact_url": "https://example.com/contact",
            "accessibilite": {
                "transport_station_presence": True,
                "transport_information": "string",
                "stationnement_presence": True,
                "stationnement_pmr": True,
                "stationnement_ext_presence": True,
                "stationnement_ext_pmr": True,
                "cheminement_ext_presence": True,
                "cheminement_ext_plain_pied": True,
                "cheminement_ext_terrain_stable": True,
                "cheminement_ext_nombre_marches": 32767,
                "cheminement_ext_sens_marches": "montant",
                "cheminement_ext_reperage_marches": True,
                "cheminement_ext_main_courante": True,
                "cheminement_ext_rampe": "aucune",
                "cheminement_ext_ascenseur": True,
                "cheminement_ext_pente_presence": True,
                "cheminement_ext_pente_degre_difficulte": "légère",
                "cheminement_ext_pente_longueur": "courte",
                "cheminement_ext_devers": "aucun",
                "cheminement_ext_bande_guidage": True,
                "cheminement_ext_retrecissement": True,
                "entree_reperage": True,
                "entree_porte_presence": True,
                "entree_porte_manoeuvre": "battante",
                "entree_porte_type": "manuelle",
                "entree_vitree": True,
                "entree_vitree_vitrophanie": True,
                "entree_plain_pied": True,
                "entree_marches": 32767,
                "entree_marches_sens": "montant",
                "entree_marches_reperage": True,
                "entree_marches_main_courante": True,
                "entree_marches_rampe": "aucune",
                "entree_balise_sonore": True,
                "entree_dispositif_appel": True,
                "entree_dispositif_appel_type": ["bouton"],
                "entree_aide_humaine": True,
                "entree_ascenseur": True,
                "entree_largeur_mini": 32767,
                "entree_pmr": True,
                "entree_pmr_informations": "string",
                "accueil_visibilite": True,
                "accueil_personnels": "aucun",
                "accueil_audiodescription_presence": True,
                "accueil_audiodescription": ["avec_équipement_permanent"],
                "accueil_equipements_malentendants_presence": True,
                "accueil_equipements_malentendants": ["bim"],
                "accueil_cheminement_plain_pied": True,
                "accueil_cheminement_nombre_marches": 32767,
                "accueil_cheminement_sens_marches": "montant",
                "accueil_cheminement_reperage_marches": True,
                "accueil_cheminement_main_courante": True,
                "accueil_cheminement_rampe": "aucune",
                "accueil_cheminement_ascenseur": True,
                "accueil_retrecissement": True,
                "sanitaires_presence": True,
                "sanitaires_adaptes": True,
                "labels": ["th"],
                "labels_familles_handicap": ["auditif"],
                "labels_autre": "string",
                "commentaire": "string",
                "conformite": True,
            },
            "source": "acceslibre",
            "source_id": "string",
            "asp_id": "string",
        }

        response = api_client.post(reverse("erp-list"), data=payload, format="json")
        assert response.status_code == 201, response.json()
        assert (erp := Erp.objects.filter(nom="Mairie de Montreuil").first())
        assert erp.published is True
        assert erp.activite.slug == "mairie"
        assert erp.accessibilite.transport_station_presence is True

        response = api_client.post(reverse("erp-list"), data=payload, format="json")
        assert response.status_code == 400, response.json()
        assert "Potentiel doublon" in response.json()["non_field_errors"][0], "Should raise for duplicated ERP"

        payload["activite"] = "Activité inconnue"
        response = api_client.post(reverse("erp-list"), data=payload, format="json")
        assert response.status_code == 400
        assert response.json() == {"activite": ["L'object avec nom=Activité inconnue n'existe pas."]}

        payload = {"accessibilite": {"transport_station_presence": False}}
        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 200, response.json()
        erp.accessibilite.refresh_from_db()
        assert erp.accessibilite.transport_station_presence is False, "Should change access info"

        payload = {"accessibilite": {"transport_station_presence": None}}
        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 200, response.json()
        erp.accessibilite.refresh_from_db()
        assert erp.accessibilite.transport_station_presence is False, "Should not be able to empty things"


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
