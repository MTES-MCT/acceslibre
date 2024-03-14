import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import ANY

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from erp.models import Accessibilite, Erp
from tests.factories import AccessibiliteFactory, ActiviteFactory, ErpFactory


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
        assert erp_json["published"] is True
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

    def test_list_can_show_drafts(self, api_client, data):
        ErpFactory(published=False)

        response = api_client.get(reverse("erp-list"))
        assert response.status_code == 200
        content = json.loads(response.content)
        assert len(content["results"]) == 1

        response = api_client.get(reverse("erp-list") + "?with_drafts=True")
        assert response.status_code == 200
        content = json.loads(response.content)
        assert len(content["results"]) == 2
        assert len([erp for erp in content["results"] if erp["published"] is False]) == 1

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
            "ban_id": "abcd_12345",
            "siret": "52128577500016",
            "telephone": None,
            "site_internet": None,
            "contact_email": None,
            "contact_url": None,
            "user_type": "system",
            "created_at": ANY,
            "updated_at": ANY,
            "published": True,
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

    def test_post_patch(self, api_client, activite, commune_montreuil):
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
        erp_json = response.json()
        assert "slug" in erp_json
        assert erp_json["nom"] == "Mairie de Montreuil"
        assert (erp := Erp.objects.filter(nom="Mairie de Montreuil").first())
        assert erp.published is True
        assert erp.activite.slug == "mairie"
        assert erp.accessibilite.transport_station_presence is True

        response = api_client.post(reverse("erp-list"), data=payload, format="json")
        assert response.status_code == 400, response.json()
        reason = response.json()["non_field_errors"][0]
        assert "Potentiel doublon" in reason, "Should raise for duplicated ERP"
        assert erp.slug in reason
        assert str(erp.id) in reason

        payload["activite"] = "Activité inconnue"
        response = api_client.post(reverse("erp-list"), data=payload, format="json")
        assert response.status_code == 400
        assert response.json() == {"activite": ["L'object avec nom=Activité inconnue n'existe pas."]}

        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data={}, format="json")
        assert response.status_code == 400, "invalid payload should raise a 400 error"

        payload = {"accessibilite": {"transport_station_presence": False, "commentaire": "New comment"}}
        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 200, response.json()
        erp.accessibilite.refresh_from_db()
        assert erp.accessibilite.transport_station_presence is False, "Should change access info"
        assert erp.accessibilite.commentaire == "New comment"

        payload = {"accessibilite": {"commentaire": "Updated comment"}}
        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 200, response.json()
        erp.accessibilite.refresh_from_db()
        assert erp.accessibilite.transport_station_presence is False, "Should kept access info"
        assert erp.accessibilite.commentaire == "Updated comment"

        payload = {"accessibilite": {"transport_station_presence": None}}
        response = api_client.patch(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 200, response.json()
        erp.accessibilite.refresh_from_db()
        assert erp.accessibilite.transport_station_presence is False, "Should not be able to empty things"

        response = api_client.delete(reverse("erp-detail", kwargs={"slug": erp.slug}), data=payload, format="json")
        assert response.status_code == 405
        erp.refresh_from_db()
        assert erp is not None, "should not be able to delete an ERP via API"

    @pytest.mark.parametrize(
        "names, q, expected",
        (
            (
                ["Musée du Louvre", "Lieu culturel", "Culture", "Cultura"],
                "Cultura",
                ["Cultura", "Culture", "Lieu culturel", "Musée du Louvre"],
            ),
            (
                ["Musée du Louvre", "Lieu culturel", "Culture", "Cultura"],
                "Culture",
                ["Culture", "Cultura", "Lieu culturel", "Musée du Louvre"],
            ),
        ),
    )
    @pytest.mark.django_db
    def test_search_name_ranking(self, api_client, names, q, expected):
        activity = ActiviteFactory(nom="Culture", mots_cles=["culture", "musée", "exposition"])
        for name in names:
            ErpFactory(nom=name, activite=activity)

        unrelated_erp = ErpFactory(nom="nothing related")

        response = api_client.get(f"{reverse('erp-list')}?q={q}")

        assert response.status_code == 200
        response_names = [erp["nom"] for erp in response.json()["results"]]
        assert response_names == expected
        assert unrelated_erp.nom not in response_names


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


@pytest.mark.django_db
@pytest.mark.usefixtures("api_client")
def test_list_can_filter_on_date(api_client):
    date = datetime.now() - timedelta(days=10)

    erp = ErpFactory(published=True)
    Erp.objects.update(created_at=date, updated_at=date)
    AccessibiliteFactory(erp=erp, created_at=date, updated_at=date)
    Accessibilite.objects.update(created_at=date, updated_at=date)

    response = api_client.get(reverse("erp-list") + "?created_or_updated_in_last_days=2")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

    response = api_client.get(reverse("erp-list") + "?created_or_updated_in_last_days=15")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


@pytest.mark.usefixtures("api_client")
class TestWidgetApi:
    @pytest.mark.django_db
    def test_nominal_case(self, api_client):
        access_infos = {
            "stationnement_presence": True,
            "stationnement_pmr": True,
            "cheminement_ext_presence": True,
            "cheminement_ext_terrain_stable": False,
            "entree_plain_pied": False,
            "entree_marches_rampe": "amovible",
            "entree_largeur_mini": 79,
            "accueil_personnels": "non-formés",
            "entree_balise_sonore": True,
            "accueil_audiodescription_presence": True,
            "accueil_audiodescription": ["avec_équipement_occasionnel"],
            "accueil_equipements_malentendants_presence": True,
            "accueil_equipements_malentendants": ["bim", "bmp"],
            "sanitaires_presence": True,
            "sanitaires_adaptes": False,
            "accueil_chambre_nombre_accessibles": 2,
        }

        erp = ErpFactory(published=True)
        AccessibiliteFactory(erp=erp, **access_infos)

        response = api_client.get(reverse("erp-widget", kwargs={"slug": erp.slug}))
        assert response.status_code == 200

        expected = {
            "slug": erp.slug,
            "sections": [
                {
                    "title": "stationnement",
                    "labels": ["Stationnement adapté dans l'établissement"],
                    "icon": "http://testserver/static/img/car.png",
                },
                {
                    "title": "accès",
                    "labels": ["Difficulté sur le chemin d'accès", "Entrée rendue accessible par rampe mais étroite"],
                    "icon": "http://testserver/static/img/path.png",
                },
                {
                    "title": "personnel",
                    "labels": ["Personnel non formé"],
                    "icon": "http://testserver/static/img/people.png",
                },
                {
                    "title": "balise sonore",
                    "labels": ["Balise sonore"],
                    "icon": "http://testserver/static/img/people.png",
                },
                {
                    "title": "audiodescription",
                    "labels": ["avec équipement occasionnel selon la programmation"],
                    "icon": "http://testserver/static/img/audiodescription.png",
                },
                {
                    "title": "équipements sourd et malentendant",
                    "labels": ANY,  # tested later on
                    "icon": "http://testserver/static/img/assistive-listening-systems.png",
                },
                {
                    "title": "sanitaire",
                    "labels": ["Sanitaire non adapté"],
                    "icon": "http://testserver/static/img/wc.png",
                },
                {
                    "title": "chambres accessibles",
                    "labels": ["2 chambres accessibles"],
                    "icon": "http://testserver/static/img/chambre_accessible.png",
                },
            ],
        }

        assert response.json() == expected
        # isolated test for unordered string on "équipements sourd et malentendant"
        for entry in response.json()["sections"]:
            if entry["title"] == "équipements sourd et malentendant":
                assert "boucle à induction magnétique fixe" in entry["labels"][0]
                assert "boucle à induction magnétique portative" in entry["labels"][0]
                break

    @pytest.mark.django_db
    def test_low_completion_case(self, api_client):

        access_infos = {
            "entree_plain_pied": False,
            "entree_marches_rampe": "fixe",
            "entree_largeur_mini": 80,
        }

        erp = ErpFactory(published=True)
        AccessibiliteFactory(erp=erp, **access_infos)

        response = api_client.get(reverse("erp-widget", kwargs={"slug": erp.slug}))
        assert response.status_code == 200

        expected = {
            "slug": erp.slug,
            "sections": [
                {
                    "title": "accès",
                    "labels": ["Accès à l'entrée par une rampe"],
                    "icon": "http://testserver/static/img/path.png",
                },
            ],
        }

        assert response.json() == expected

    @pytest.mark.django_db
    def test_not_found_case(self, api_client):
        response = api_client.get(reverse("erp-widget", kwargs={"slug": "unknown-slug"}))
        assert response.status_code == 404
