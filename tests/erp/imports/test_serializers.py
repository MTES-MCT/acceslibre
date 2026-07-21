import pytest
from django.contrib.gis.geos import Point

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp
from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "erp_values, is_valid, geocoder_result",
    (
        pytest.param({"siret": "Non renseigné"}, False, None, id="invalid_siret"),
        pytest.param({"siret": "48137888300021"}, True, None, id="valid_siret"),
        pytest.param({"nom": ""}, False, None, id="empty_name"),
        pytest.param({"nom": "Marie \n      Blachère"}, True, None, id="name_with_new_line"),
        pytest.param({"code_postal": "99999"}, False, None, id="invalid_postal_code"),
        pytest.param({"code_postal": "348300"}, False, None, id="invalid_postal_code"),
        pytest.param({"activite": "Unknown in DB"}, False, None, id="invalid_activity"),
        pytest.param({"commune": "Unknown in DB"}, True, None, id="invalid_commune"),
        pytest.param(
            {
                "commune": "Unknown in DB",
                "numero": "125",
                "voie": "Rue des Pompiers",
                "code_postal": "86140",
            },
            False,
            {
                "geom": Point((0, 0)),
            },
            id="invalid_ban_adresse",
        ),
        pytest.param({"accessibilite": {}}, False, None, id="empty_accessibility"),
        pytest.param({"latitude": 0, "longitude": 0}, True, {"empty": True}, id="empty_geocoder"),
        pytest.param(
            {
                "activite": "Boulangerie",
                "numero": "4",
                "voie": "grand rue",
                "code_postal": "34830",
                "commune": "Jacou",
                "email": "importator@tierce.com",
            },
            False,
            {
                "geom": Point((0, 0)),
                "numero": "4",
                "voie": "grand rue",
                "code_postal": "34830",
                "commune": "Jacou",
                "code_insee": "34830",
            },
            id="duplicate",
        ),
        pytest.param({"accessibilite": {"entree_porte_presence": 1}}, True, None, id="boolean_choices"),
        pytest.param({"accessibilite": {"entree_porte_presence": "faux"}}, True, None, id="boolean_choices"),
        pytest.param(
            {"accessibilite": {"accueil_audiodescription_presence": True, "accueil_audiodescription": ["avec_app"]}},
            True,
            None,
            id="array",
        ),
        pytest.param(
            {
                "accessibilite": {
                    "stationnement_zone_depose_pmr": "oui",
                    "accueil_physique": "sensibilise_ou_forme",
                    "accueil_aire_de_jeux": "non",
                    "accueil_tribunes": 1,
                    "accueil_tribunes_places": 3,
                    "accueil_tribunes_localisation_places": "niveau_aire_de_jeux",
                    "accueil_tribunes_places_avec_accompagnants": 2,
                    "accueil_vestiaires": "vrai",
                    "accueil_vestiaires_largeur_passage": "superieur_a_110",
                    "accueil_douches_collectives": True,
                    "accueil_douches_collectives_adaptees": True,
                    "accueil_douches_individuelles": "faux",
                    "accueil_casiers": "1",
                    "accueil_casiers_adaptes": "0",
                    "accueil_casiers_fermeture": ["serrure_avec_cle", "verrou_cadenas"],
                    "accueil_prestations_complementaires": ["score_visible"],
                    "accueil_presence_espaces_specifiques": ["presence_espace_repos_sensoriel"],
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": True,
                    "sanitaires_largeur_porte": "entre_90_et_110",
                    "sanitaires_sens_transfert": "gauche_et_droite",
                    "sanitaires_urinoirs": True,
                }
            },
            True,
            None,
            id="sports_equipment",
        ),
        pytest.param(
            {"accessibilite": {"accueil_casiers_fermeture": ["unknown_lock"]}},
            False,
            None,
            id="sports_equipment_invalid_array_choice",
        ),
        pytest.param(
            {"accessibilite": {"accueil_physique": "unknown"}},
            False,
            None,
            id="sports_equipment_invalid_choice",
        ),
        pytest.param(
            # sanitaires_adaptes is not True, so its children must stay empty
            {"accessibilite": {"sanitaires_presence": True, "sanitaires_largeur_porte": "entre_80_et_90"}},
            False,
            None,
            id="sports_equipment_inconsistent_sanitaires",
        ),
    ),
)
def test_erp_import_serializer(mocker, erp_values, is_valid, geocoder_result):
    activite = ActiviteFactory(nom="Boulangerie")
    CommuneFactory(nom="Jacou")
    CommuneFactory(nom="Paris")
    erp = ErpFactory(commune="Jacou", numero="4", voie="grand rue", code_postal="34380", activite=activite, siret="")

    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value=geocoder_result
        or {
            "geom": Point((0, 0), srid=4326),
            "numero": "4",
            "voie": "Rue de la Paix",
            "lieu_dit": None,
            "code_postal": "75002",
            "commune": "Paris",
            "code_insee": "75111",
            "provider": "ban",
        },
    )

    initial_values = {
        "voie": "Rue de la Coquille",
        "code_postal": 34830,
        "commune": "Jacou",
        "nom": "Marie Blachère",
        "activite": "Boulangerie",
        "accessibilite": {"entree_porte_presence": True},
        "latitude": 5,
        "longitude": 56,
    }
    serializer = ErpImportSerializer(data=initial_values | erp_values)

    assert serializer.is_valid() is is_valid, f"{serializer.errors}"

    if is_valid:
        erp = serializer.save()
        assert isinstance(erp, Erp)
        assert erp.activite
        assert erp.nom == "Marie Blachère"
        assert erp.accessibilite
        assert erp.geom.x == erp.geom.y == 0
        assert erp.import_email == erp_values.get("email")


@pytest.mark.django_db
def test_erp_update_serializer():
    erp = ErpFactory(nom="Initial name", accessibilite__accueil_equipements_malentendants_presence=False)

    serializer = ErpImportSerializer(
        instance=erp,
        data={
            "accessibilite": {
                "accueil_equipements_malentendants_presence": True,
                "accueil_audiodescription_presence": True,
                "accueil_audiodescription": ["avec_app"],
            },
            "nom": "Aux bons pains",
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    erp.refresh_from_db()
    assert erp.nom != "Aux bons pains", "Name should not be editable"
    assert erp.accessibilite.accueil_equipements_malentendants_presence is True
    assert erp.accessibilite.accueil_audiodescription_presence is True
    assert erp.accessibilite.accueil_audiodescription == ["avec_app"]


@pytest.mark.django_db
def test_erp_update_serializer_inconsistencies():
    erp = ErpFactory(
        nom="Initial name",
        accessibilite__accueil_audiodescription_presence=True,
        accessibilite__accueil_audiodescription=["avec_app"],
        accessibilite__entree_plain_pied=False,
        accessibilite__entree_ascenseur=True,
        accessibilite__entree_ascenseur_pmr=True,
        accessibilite__accueil_chambre_nombre_accessibles=1,
        accessibilite__accueil_chambre_douche_siege=True,
        accessibilite__accueil_cheminement_plain_pied=False,  # control
        accessibilite__accueil_cheminement_ascenseur=True,  # control
        accessibilite__accueil_cheminement_ascenseur_pmr=True,  # control
    )

    serializer = ErpImportSerializer(
        instance=erp,
        data={
            "accessibilite": {
                "accueil_audiodescription_presence": False,
                "entree_plain_pied": True,
                "accueil_chambre_nombre_accessibles": 0,
            },
            "nom": "Aux bons pains",
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    erp.refresh_from_db()
    assert erp.nom != "Aux bons pains", "Name should not be editable"
    assert erp.accessibilite.accueil_audiodescription_presence is False
    assert erp.accessibilite.accueil_audiodescription == [], "should have reinit child of attr switched to False"
    assert erp.accessibilite.entree_plain_pied is True
    assert erp.accessibilite.entree_ascenseur is None, "should have reinit child"
    assert erp.accessibilite.entree_ascenseur_pmr is None, "should have reinit child of child"
    assert erp.accessibilite.accueil_chambre_nombre_accessibles == 0
    assert erp.accessibilite.accueil_chambre_douche_siege is None, "should have reinit child of attr switched to 0"
    assert erp.accessibilite.accueil_cheminement_plain_pied is False, "control, should not be reinit"
    assert erp.accessibilite.accueil_cheminement_ascenseur is True, "control, should not be reinit"
    assert erp.accessibilite.accueil_cheminement_ascenseur_pmr is True, "control, should not be reinit"


@pytest.mark.django_db
def test_erp_import_serializer_sports_equipment(mocker):
    ActiviteFactory(nom="Gymnase")
    CommuneFactory(nom="Jacou")
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value={
            "geom": Point((0, 0), srid=4326),
            "numero": "4",
            "voie": "Rue de la Paix",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34120",
            "provider": "ban",
        },
    )

    serializer = ErpImportSerializer(
        data={
            "voie": "Rue de la Coquille",
            "code_postal": 34830,
            "commune": "Jacou",
            "nom": "Gymnase Jean Moulin",
            "activite": "Gymnase",
            "accessibilite": {
                "stationnement_zone_depose_pmr": "oui",
                "accueil_physique": "non_forme",
                "accueil_aire_de_jeux": "non",
                "accueil_tribunes": "vrai",
                "accueil_tribunes_places": 3,
                "accueil_tribunes_localisation_places": "reparti_differents_niveaux",
                "accueil_tribunes_places_avec_accompagnants": 1,
                "accueil_vestiaires": 1,
                "accueil_vestiaires_largeur_passage": "entre_90_et_110",
                "accueil_douches_collectives": "1",
                "accueil_douches_collectives_adaptees": "0",
                "accueil_douches_individuelles": "faux",
                "accueil_casiers": True,
                "accueil_casiers_adaptes": "oui",
                "accueil_casiers_fermeture": ["serrure_electronique_a_code", "autre"],
                "accueil_prestations_complementaires": ["sonorisation_arbitrage", "score_visible"],
                "accueil_presence_espaces_specifiques": ["presence_espace_chiens_guides"],
                "sanitaires_presence": "oui",
                "sanitaires_adaptes": "oui",
                "sanitaires_largeur_porte": "entre_80_et_90",
                "sanitaires_sens_transfert": "gauche_et_droite",
                "sanitaires_urinoirs": "non",
            },
        }
    )

    assert serializer.is_valid(), serializer.errors
    erp = serializer.save()

    access = erp.accessibilite
    assert access.stationnement_zone_depose_pmr is True
    assert access.accueil_physique == "non_forme"
    assert access.accueil_aire_de_jeux is False
    assert access.accueil_tribunes is True
    assert access.accueil_tribunes_places == 3
    assert access.accueil_tribunes_localisation_places == "reparti_differents_niveaux"
    assert access.accueil_tribunes_places_avec_accompagnants == 1
    assert access.accueil_vestiaires is True
    assert access.accueil_vestiaires_largeur_passage == "entre_90_et_110"
    assert access.accueil_douches_collectives is True
    assert access.accueil_douches_collectives_adaptees is False
    assert access.accueil_douches_individuelles is False
    assert access.accueil_casiers is True
    assert access.accueil_casiers_adaptes is True
    assert access.accueil_casiers_fermeture == ["serrure_electronique_a_code", "autre"]
    assert access.accueil_prestations_complementaires == ["sonorisation_arbitrage", "score_visible"]
    assert access.accueil_presence_espaces_specifiques == ["presence_espace_chiens_guides"]
    assert access.sanitaires_presence is True
    assert access.sanitaires_adaptes is True
    assert access.sanitaires_largeur_porte == "entre_80_et_90"
    assert access.sanitaires_sens_transfert == "gauche_et_droite"
    assert access.sanitaires_urinoirs is False


@pytest.mark.django_db
def test_erp_update_serializer_sports_equipment_inconsistencies():
    erp = ErpFactory(
        accessibilite__accueil_tribunes=True,
        accessibilite__accueil_tribunes_places=4,
        accessibilite__accueil_tribunes_localisation_places="niveau_aire_de_jeux",
        accessibilite__accueil_tribunes_places_avec_accompagnants=2,
        accessibilite__accueil_vestiaires=True,
        accessibilite__accueil_vestiaires_largeur_passage="superieur_a_110",
        accessibilite__accueil_casiers=True,
        accessibilite__accueil_casiers_adaptes=True,
        accessibilite__accueil_casiers_fermeture=["serrure_avec_cle"],
        accessibilite__accueil_douches_collectives=True,  # control
        accessibilite__accueil_douches_collectives_adaptees=True,  # control
        accessibilite__sanitaires_presence=True,
        accessibilite__sanitaires_adaptes=True,
        accessibilite__sanitaires_largeur_porte="entre_90_et_110",
        accessibilite__sanitaires_sens_transfert="gauche",
        accessibilite__sanitaires_urinoirs=True,
    )

    serializer = ErpImportSerializer(
        instance=erp,
        data={
            "accessibilite": {
                "accueil_tribunes_places": 0,
                "accueil_vestiaires": False,
                "accueil_casiers": "non",
                # sanitaires_presence is repeated as a partial payload is validated on its own
                "sanitaires_presence": True,
                "sanitaires_adaptes": False,
            }
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    erp.refresh_from_db()
    access = erp.accessibilite
    assert access.accueil_tribunes_places == 0
    assert access.accueil_tribunes_localisation_places is None, "should have reinit child of attr switched to 0"
    assert access.accueil_tribunes_places_avec_accompagnants is None, "should have reinit child of attr switched to 0"
    assert access.accueil_vestiaires is False
    assert access.accueil_vestiaires_largeur_passage is None, "should have reinit child"
    assert access.accueil_casiers is False
    assert access.accueil_casiers_adaptes is None, "should have reinit child"
    assert access.accueil_casiers_fermeture == [], "should have reinit array child"
    assert access.sanitaires_adaptes is False
    assert access.sanitaires_largeur_porte is None, "should have reinit child"
    assert access.sanitaires_sens_transfert is None, "should have reinit child"
    assert access.accueil_douches_collectives is True, "control, should not be reinit"
    assert access.accueil_douches_collectives_adaptees is True, "control, should not be reinit"


@pytest.mark.django_db
def test_erp_update_serializer_keeps_children_above_min_value():
    erp = ErpFactory(
        accessibilite__accueil_tribunes=True,
        accessibilite__accueil_tribunes_places=4,
        accessibilite__accueil_tribunes_localisation_places="niveau_aire_de_jeux",
        accessibilite__accueil_tribunes_places_avec_accompagnants=2,
    )

    serializer = ErpImportSerializer(
        instance=erp,
        data={"accessibilite": {"accueil_tribunes_places": 8}},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    erp.refresh_from_db()
    access = erp.accessibilite
    assert access.accueil_tribunes_places == 8
    assert access.accueil_tribunes_localisation_places == "niveau_aire_de_jeux", "children must be kept above min value"
    assert access.accueil_tribunes_places_avec_accompagnants == 2, "children must be kept above min value"


@pytest.mark.django_db
def test_erp_duplicate():
    boulangerie = ActiviteFactory(nom="Boulangerie")
    # 3/43 must match geocode mock coordinates
    erp = ErpFactory(geom=Point(3, 43), activite=boulangerie)

    ActiviteFactory(nom="Piscine")
    initial_values = {
        "numero": erp.numero,
        "voie": erp.voie,
        "code_postal": erp.code_postal,
        "commune": erp.commune,
        "nom": "Marie Blachère",
        "activite": "Boulangerie",
        "accessibilite": {"entree_porte_presence": True},
        "latitude": erp.geom.x,
        "longitude": erp.geom.y,
    }
    serializer = ErpImportSerializer(data=initial_values)

    assert serializer.is_valid() is False
    assert "Potentiel doublon par activité/adresse postale" in str(serializer.errors["non_field_errors"])

    initial_values = {
        "numero": erp.numero,
        "voie": erp.voie,
        "code_postal": erp.code_postal,
        "commune": erp.commune,
        "nom": erp.nom,
        "activite": "Piscine",
        "accessibilite": {"entree_porte_presence": True},
        "latitude": erp.geom.x,
        "longitude": erp.geom.y,
    }
    serializer = ErpImportSerializer(data=initial_values)

    assert serializer.is_valid() is False
    assert "Potentiel doublon par nom/75m" in str(serializer.errors["non_field_errors"])
