import csv

import pytest
from django.core.management import call_command

from erp.management.commands.import_doctolib import Command
from erp.models import Accessibilite, Activite, Erp, ExternalSource
from tests.factories import ActiviteFactory, ErpFactory


def _record(**overrides):
    record = {
        "id docto": "123456",
        "id acceslibre final sans": "",
        "Nom": "Cabinet médical",
        "Activité corrigée": "Médecin généraliste",
        "numero": "1",
        "voie": "Rue de la Paix",
        "code_postal": "75002",
        "commune": "Paris",
        "latitude": "48.86",
        "longitude": "2.34",
        "rpps": "10000000001",
        "wheelchair_route.has_accessible_parking_nearby": "",
        "wheelchair_route.has_accessible_path_to_entrance": "",
        "equipment.has_floor_guiding_strips": "",
        "wheelchair_route.has_automatic_doors": "",
        "wheelchair_route.has_step_free_access": "",
        "elevator.present": "",
        "elevator.has_min_width": "",
        "stairs.handrail": "",
        "intercom.present": "",
        "patient_reception.has_staff_assistance": "",
        "wheelchair_route.has_min_width": "",
        "equipment.has_accessible_restroom": "",
        "patient_reception.has_provider_disability_experience": "",
    }
    record.update(overrides)
    return record


class TestAccessibilityMapping:
    def test_blank_fields_produce_no_accessibility_data(self):
        assert Command._accessibilite(_record()) == {}

    def test_combines_doctolib_fields(self):
        data = Command._accessibilite(
            _record(
                **{
                    "wheelchair_route.has_accessible_parking_nearby": "true",
                    "wheelchair_route.has_accessible_path_to_entrance": "true",
                    "equipment.has_floor_guiding_strips": "true",
                    "wheelchair_route.has_automatic_doors": "true",
                    "wheelchair_route.has_step_free_access": "true",
                    "elevator.present": "true",
                    "elevator.has_min_width": "true",
                    "stairs.handrail": "true",
                    "intercom.present": "true",
                    "patient_reception.has_staff_assistance": "true",
                    "wheelchair_route.has_min_width": "true",
                    "equipment.has_accessible_restroom": "true",
                    "patient_reception.has_provider_disability_experience": "true",
                }
            )
        )

        assert data["stationnement_ext_presence"] is True
        assert data["stationnement_ext_pmr"] is True
        assert data["cheminement_ext_presence"] is True
        assert data["cheminement_ext_plain_pied"] is True
        assert data["cheminement_ext_bande_guidage"] is True
        assert data["entree_porte_presence"] is True
        assert data["entree_porte_type"] == "automatique"
        assert data["entree_plain_pied"] is True
        assert data["accueil_cheminement_plain_pied"] is True
        assert "accueil_cheminement_ascenseur" not in data
        assert "accueil_cheminement_main_courante" not in data
        assert data["entree_dispositif_appel"] is True
        assert data["entree_dispositif_appel_type"] == ["interphone"]
        assert data["entree_aide_humaine"] is True
        assert data["accueil_personnels"] == "formés"
        assert data["entree_largeur_mini"] == 80
        assert data["accueil_retrecissement"] is False
        assert data["sanitaires_presence"] is True
        assert data["sanitaires_adaptes"] is True
        assert data["accueil_soignant"] is True

    def test_false_values_do_not_create_inconsistent_children(self):
        data = Command._accessibilite(
            _record(
                **{
                    "wheelchair_route.has_accessible_parking_nearby": "false",
                    "wheelchair_route.has_accessible_path_to_entrance": "false",
                    "wheelchair_route.has_automatic_doors": "false",
                    "elevator.present": "false",
                    "stairs.handrail": "none",
                    "intercom.present": "false",
                    "patient_reception.has_staff_assistance": "false",
                    "equipment.has_accessible_restroom": "false",
                    "patient_reception.has_provider_disability_experience": "false",
                }
            )
        )

        assert data["stationnement_ext_presence"] is False
        assert "stationnement_ext_pmr" not in data
        assert data["cheminement_ext_presence"] is True
        assert data["cheminement_ext_plain_pied"] is False
        assert data["entree_porte_presence"] is True
        assert data["entree_porte_type"] == "manuelle"
        assert data["accueil_cheminement_ascenseur"] is False
        assert data["accueil_cheminement_main_courante"] is False
        assert data["entree_dispositif_appel"] is False
        assert "entree_dispositif_appel_type" not in data
        assert data["entree_aide_humaine"] is False
        assert "accueil_personnels" not in data
        assert data["sanitaires_presence"] is False
        assert "sanitaires_adaptes" not in data
        assert data["accueil_soignant"] is False

    def test_dry_run_and_sources(self):
        sources = Command._sources(_record())

        assert sources == [
            {"source": ExternalSource.SOURCE_DOCTOLIB, "source_id": "123456"},
            {"source": ExternalSource.SOURCE_ANNUAIRE_SANTE, "source_id": "10000000001"},
        ]


class TestExistingAccessibility:
    def test_build_data_keeps_existing_parent_for_validation(self):
        erp = Erp(
            nom="Cabinet existant",
            commune="Paris",
            code_postal="75002",
            numero="1",
            voie="Rue de la Paix",
            activite=Activite(nom="Médecin généraliste"),
        )
        erp.accessibilite = Accessibilite(entree_porte_presence=True)

        accessibility = Command._filter_existing_accessibility(
            Command._accessibilite(_record(**{"wheelchair_route.has_automatic_doors": "true"})),
            erp,
        )
        data = Command._build_data(_record(**{"wheelchair_route.has_automatic_doors": "true"}), erp, accessibility)

        assert data["accessibilite"]["entree_porte_presence"] is True
        assert data["accessibilite"]["entree_porte_type"] == "automatique"

    def test_does_not_add_a_child_when_existing_parent_is_false(self):
        erp = Erp()
        erp.accessibilite = Accessibilite(entree_porte_presence=False)

        data = Command._filter_existing_accessibility(
            Command._accessibilite(_record(**{"wheelchair_route.has_automatic_doors": "true"})),
            erp,
        )

        assert "entree_porte_presence" not in data
        assert "entree_porte_type" not in data

    def test_fills_an_existing_empty_list(self):
        erp = Erp()
        erp.accessibilite = Accessibilite(entree_dispositif_appel=True, entree_dispositif_appel_type=[])

        data = Command._filter_existing_accessibility(
            Command._accessibilite(_record(**{"intercom.present": "true"})),
            erp,
        )

        assert data["entree_dispositif_appel_type"] == ["interphone"]

    def test_does_not_add_a_child_when_existing_plain_pied_is_true(self):
        erp = Erp()
        erp.accessibilite = Accessibilite(accueil_cheminement_plain_pied=True)

        data = Command._filter_existing_accessibility(
            Command._accessibilite(
                _record(
                    **{
                        "wheelchair_route.has_step_free_access": "false",
                        "elevator.present": "true",
                        "elevator.has_min_width": "true",
                        "stairs.handrail": "true",
                    }
                )
            ),
            erp,
        )

        assert "accueil_cheminement_plain_pied" not in data
        assert "accueil_cheminement_ascenseur" not in data
        assert "accueil_cheminement_ascenseur_pmr" not in data
        assert "accueil_cheminement_main_courante" not in data


@pytest.mark.django_db
def test_command_updates_existing_erp_without_overwriting(tmp_path):
    ActiviteFactory(nom="Médecin généraliste")
    erp = ErpFactory(
        pk=42,
        nom="Cabinet existant",
        commune="Paris",
        code_postal="75002",
        activite__nom="Médecin généraliste",
        with_accessibility=True,
        accessibilite__entree_porte_presence=True,
        accessibilite__entree_porte_type="manuelle",
        accessibilite__entree_aide_humaine=False,
    )

    csv_path = tmp_path / "doctolib.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(_record().keys()))
        writer.writeheader()
        writer.writerow(
            _record(
                **{
                    "id acceslibre final sans": "42",
                    "Nom": "Nom ignoré",
                    "wheelchair_route.has_automatic_doors": "true",
                    "patient_reception.has_staff_assistance": "true",
                    "equipment.has_accessible_restroom": "true",
                }
            )
        )

    call_command("import_doctolib", file=str(csv_path))

    erp.refresh_from_db()
    erp.accessibilite.refresh_from_db()

    assert Erp.objects.count() == 1
    assert erp.nom == "Cabinet existant"
    assert erp.accessibilite.entree_porte_presence is True
    assert erp.accessibilite.entree_porte_type == "manuelle"
    assert erp.accessibilite.entree_aide_humaine is False
    assert erp.accessibilite.accueil_personnels is None
    assert erp.accessibilite.sanitaires_presence is True
    assert erp.accessibilite.sanitaires_adaptes is True
    assert erp.sources.get(source=ExternalSource.SOURCE_DOCTOLIB).source_id == "123456"
    assert erp.sources.get(source=ExternalSource.SOURCE_ANNUAIRE_SANTE).source_id == "10000000001"


@pytest.mark.django_db
def test_command_creates_erp_and_skips_blank_names(tmp_path):
    ActiviteFactory(nom="Médecin généraliste")

    csv_path = tmp_path / "doctolib.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(_record().keys()))
        writer.writeheader()
        writer.writerow(
            _record(
                **{
                    "wheelchair_route.has_step_free_access": "true",
                    "intercom.present": "true",
                }
            )
        )
        writer.writerow(_record(**{"id docto": "999999", "Nom": " ", "rpps": ""}))

    call_command("import_doctolib", file=str(csv_path))

    assert Erp.objects.count() == 1
    erp = Erp.objects.get()
    assert erp.nom == "Cabinet médical"
    assert erp.accessibilite.entree_plain_pied is True
    assert erp.accessibilite.accueil_cheminement_plain_pied is True
    assert erp.accessibilite.entree_dispositif_appel is True
    assert erp.accessibilite.entree_dispositif_appel_type == ["interphone"]
    assert erp.sources.get(source=ExternalSource.SOURCE_DOCTOLIB).source_id == "123456"
    assert erp.sources.get(source=ExternalSource.SOURCE_ANNUAIRE_SANTE).source_id == "10000000001"
