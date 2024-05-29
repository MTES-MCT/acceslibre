from contextlib import nullcontext as does_not_raise

import pytest
import reversion
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from erp.exceptions import MergeException
from erp.models import Accessibilite, Activite, ActivitySuggestion, Erp
from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory, UserFactory


@pytest.mark.django_db
class TestAccessibility:
    @pytest.mark.parametrize(
        "other, expected",
        (
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": False,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                },
                True,
                id="same",
            ),
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": True,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                },
                False,
                id="not_the_same",
            ),
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": True,
                    "commentaire": "foo",
                    "entree_porte_presence": True,
                    "entree_reperage": True,
                    "stationnement_presence": True,
                },
                False,
                id="more_attrs",
            ),
            pytest.param({"sanitaires_adaptes": False}, False, id="less_attrs"),
        ),
    )
    def test_equals(self, other, expected):
        access = AccessibiliteFactory(
            sanitaires_presence=True,
            sanitaires_adaptes=False,
            commentaire="foo",
            entree_porte_presence=True,
            entree_reperage=True,
        )
        other = Accessibilite(**other)
        assert (access == other) is expected

    def test_has_data(self):
        erp = ErpFactory(
            accessibilite__sanitaires_presence=True,
            accessibilite__sanitaires_adaptes=False,
            accessibilite__commentaire="foo",
            accessibilite__entree_porte_presence=True,
            accessibilite__entree_reperage=True,
        )

        acc = Accessibilite(id=1337, erp=erp)
        assert acc.has_data() is False

        acc = Accessibilite(id=1337, erp=erp, stationnement_presence=True)
        assert acc.has_data() is True

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "transport_station_presence": False,
                    "transport_information": "A côté de l'arrêt de bus",
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "transport_station_presence": None,
                    "transport_information": "A côté de l'arrêt de bus",
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "transport_station_presence": False,
                    "transport_information": "",
                },
                False,
                id="empty_valid",
            ),
            pytest.param(
                {
                    "transport_station_presence": False,
                    "transport_information": None,
                },
                False,
                id="null_valid",
            ),
            pytest.param(
                {
                    "transport_station_presence": True,
                    "transport_information": None,
                },
                False,
                id="nominal",
            ),
        ),
    )
    def test_constraint_transport(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "stationnement_presence": False,
                    "stationnement_pmr": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "stationnement_presence": False,
                    "stationnement_pmr": True,
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "stationnement_presence": False,
                    "stationnement_pmr": None,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "stationnement_presence": True,
                    "stationnement_pmr": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "stationnement_ext_presence": False,
                    "stationnement_ext_pmr": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "stationnement_ext_presence": None,
                    "stationnement_ext_pmr": True,
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "stationnement_ext_presence": False,
                    "stationnement_ext_pmr": None,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "stationnement_ext_presence": True,
                    "stationnement_ext_pmr": True,
                },
                False,
                id="nominal",
            ),
        ),
    )
    def test_constraint_stationnement_and_ext(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_plain_pied": False,
                    "cheminement_ext_nombre_marches": 2,
                    "cheminement_ext_reperage_marches": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_plain_pied": True,
                    "cheminement_ext_nombre_marches": 0,
                },
                True,
                id="valid_0",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_plain_pied": True,
                    "cheminement_ext_nombre_marches": 2,
                    "cheminement_ext_reperage_marches": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_plain_pied": None,
                    "cheminement_ext_nombre_marches": 2,
                    "cheminement_ext_reperage_marches": True,
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_pente_presence": True,
                    "cheminement_ext_pente_longueur": 2,
                },
                False,
                id="nominal_pente",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_pente_presence": True,
                    "cheminement_ext_pente_longueur": None,
                },
                False,
                id="nominal_pente_none",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_pente_presence": False,
                    "cheminement_ext_pente_longueur": 2,
                },
                True,
                id="invalid_pente",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_pente_presence": None,
                    "cheminement_ext_pente_longueur": 2,
                },
                True,
                id="invalid_pente_none",
            ),
        ),
    )
    def test_constraint_cheminement_ext_plain_pied_and_pente(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "cheminement_ext_presence": True,
                    "cheminement_ext_terrain_stable": True,
                    "cheminement_ext_plain_pied": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": False,
                    "cheminement_ext_terrain_stable": True,
                    "cheminement_ext_plain_pied": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "cheminement_ext_presence": None,
                    "cheminement_ext_terrain_stable": True,
                    "cheminement_ext_plain_pied": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_cheminement_ext_presence(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_vitree": True,
                    "entree_vitree_vitrophanie": None,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_vitree": None,
                    "entree_vitree_vitrophanie": None,
                },
                False,
                id="nominal_none",
            ),
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_vitree": False,
                    "entree_vitree_vitrophanie": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_vitree": False,
                    "entree_vitree_vitrophanie": False,
                },
                True,
                id="invalid_all_false",
            ),
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_vitree": None,
                    "entree_vitree_vitrophanie": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_entree_vitree(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "entree_porte_presence": True,
                    "entree_porte_type": "automatique",
                    "entree_vitree": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "entree_porte_presence": False,
                    "entree_porte_type": "automatique",
                    "entree_vitree": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "entree_porte_presence": None,
                    "entree_porte_type": "automatique",
                    "entree_vitree": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_entree_porte_presence(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "entree_plain_pied": False,
                    "entree_ascenseur": True,
                    "entree_marches": 1,
                    "entree_marches_main_courante": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "entree_plain_pied": False,
                    "entree_marches": 0,
                },
                False,
                id="nominal_zero",
            ),
            pytest.param(
                {
                    "entree_plain_pied": True,
                    "entree_marches": 0,
                },
                False,
                id="nominal_zero",
            ),
            pytest.param(
                {
                    "entree_plain_pied": True,
                    "entree_ascenseur": True,
                    "entree_marches": 1,
                    "entree_marches_main_courante": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "entree_plain_pied": None,
                    "entree_ascenseur": True,
                    "entree_marches": 1,
                    "entree_marches_main_courante": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_entree_plain_pied(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "entree_dispositif_appel": True,
                    "entree_dispositif_appel_type": ["visiophone"],
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "entree_dispositif_appel": False,
                    "entree_dispositif_appel_type": ["visiophone"],
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "entree_dispositif_appel": None,
                    "entree_dispositif_appel_type": ["visiophone"],
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "entree_dispositif_appel": False,
                    "entree_dispositif_appel_type": None,
                },
                False,
                id="valid_none",
            ),
            pytest.param(
                {
                    "entree_dispositif_appel": False,
                    "entree_dispositif_appel_type": [],
                },
                False,
                id="valid_empty",
            ),
        ),
    )
    def test_constraint_entree_dispositif_appel(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "entree_pmr": True,
                    "entree_pmr_informations": "entrée spécifique",
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "entree_pmr": False,
                    "entree_pmr_informations": "entrée spécifique",
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "entree_pmr": None,
                    "entree_pmr_informations": "entrée spécifique",
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "entree_pmr": False,
                    "entree_pmr_informations": None,
                },
                False,
                id="valid_none",
            ),
            pytest.param(
                {
                    "entree_pmr": False,
                    "entree_pmr_informations": "",
                },
                False,
                id="valid_empty",
            ),
        ),
    )
    def test_constraint_entree_pmr(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "accueil_cheminement_plain_pied": False,
                    "accueil_cheminement_ascenseur": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "accueil_cheminement_plain_pied": None,
                    "accueil_cheminement_ascenseur": True,
                },
                False,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "accueil_cheminement_plain_pied": True,
                    "accueil_cheminement_ascenseur": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "accueil_cheminement_plain_pied": True,
                    "accueil_cheminement_ascenseur": None,
                },
                False,
                id="valid_none",
            ),
        ),
    )
    def test_constraint_accueil_cheminement_plain_pied(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "accueil_audiodescription_presence": True,
                    "accueil_audiodescription": ["visiophone"],
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "accueil_audiodescription_presence": False,
                    "accueil_audiodescription": ["visiophone"],
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "accueil_audiodescription_presence": None,
                    "accueil_audiodescription": ["visiophone"],
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "accueil_audiodescription_presence": False,
                    "accueil_audiodescription": None,
                },
                False,
                id="valid_none",
            ),
            pytest.param(
                {
                    "accueil_audiodescription_presence": False,
                    "accueil_audiodescription": [],
                },
                False,
                id="valid_empty",
            ),
        ),
    )
    def test_constraint_accueil_audiodescription(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "accueil_equipements_malentendants_presence": True,
                    "accueil_equipements_malentendants": ["visiophone"],
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "accueil_equipements_malentendants_presence": False,
                    "accueil_equipements_malentendants": ["visiophone"],
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "accueil_equipements_malentendants_presence": None,
                    "accueil_equipements_malentendants": ["visiophone"],
                },
                True,
                id="invalid_none",
            ),
            pytest.param(
                {
                    "accueil_equipements_malentendants_presence": False,
                    "accueil_equipements_malentendants": None,
                },
                False,
                id="valid_none",
            ),
            pytest.param(
                {
                    "accueil_equipements_malentendants_presence": False,
                    "accueil_equipements_malentendants": [],
                },
                False,
                id="valid_empty",
            ),
        ),
    )
    def test_constraint_accueil_equipements_malentendants(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "sanitaires_presence": True,
                    "sanitaires_adaptes": None,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "sanitaires_presence": False,
                    "sanitaires_adaptes": None,
                },
                False,
                id="nominal_false",
            ),
            pytest.param(
                {
                    "sanitaires_presence": False,
                    "sanitaires_adaptes": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "sanitaires_presence": None,
                    "sanitaires_adaptes": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_sanitaires_presence(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "labels": ["th"],
                    "labels_familles_handicap": ["auditif", "mental"],
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {"labels": ["th"], "labels_familles_handicap": ["auditif", "mental"], "labels_autre": "autre"},
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "labels": ["th"],
                    "labels_familles_handicap": [],
                },
                False,
                id="nominal_empty",
            ),
            pytest.param(
                {
                    "labels": [],
                    "labels_familles_handicap": [],
                    "labels_autre": None,
                },
                False,
                id="nominal_empty",
            ),
            pytest.param(
                {
                    "labels": ["th"],
                    "labels_familles_handicap": None,
                },
                False,
                id="nominal_none",
            ),
            pytest.param(
                {
                    "labels": [],
                    "labels_familles_handicap": ["auditif", "mental"],
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "labels": [],
                    "labels_autre": "autre chose",
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "labels": None,
                    "labels_familles_handicap": ["auditif", "mental"],
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_labels(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "attrs, should_raise",
        (
            pytest.param(
                {
                    "accueil_chambre_nombre_accessibles": 1,
                    "accueil_chambre_douche_plain_pied": True,
                },
                False,
                id="nominal",
            ),
            pytest.param(
                {
                    "accueil_chambre_nombre_accessibles": 2,
                    "accueil_chambre_douche_plain_pied": False,
                },
                False,
                id="nominal_false",
            ),
            pytest.param(
                {
                    "accueil_chambre_nombre_accessibles": 2,
                    "accueil_chambre_douche_plain_pied": None,
                },
                False,
                id="nominal_none",
            ),
            pytest.param(
                {
                    "accueil_chambre_nombre_accessibles": 0,
                    "accueil_chambre_douche_plain_pied": True,
                },
                True,
                id="invalid",
            ),
            pytest.param(
                {
                    "accueil_chambre_nombre_accessibles": None,
                    "accueil_chambre_douche_siege": True,
                },
                True,
                id="invalid_none",
            ),
        ),
    )
    def test_constraint_chambres(self, attrs, should_raise):
        raiser = pytest.raises(IntegrityError) if should_raise else does_not_raise()

        with raiser:
            AccessibiliteFactory(**attrs).save()

    @pytest.mark.django_db
    def test_constraint_scenario(self):
        access = AccessibiliteFactory()
        access.labels = ["th"]
        access.labels_familles_handicap = ["auditif"]
        access.save()

        access.labels_familles_handicap = []
        access.save()

        access.labels_autre = "autre"
        access.save()

        with pytest.raises(IntegrityError):
            access.labels = []
            access.save()


@pytest.mark.django_db
class TestErp:
    def test_clean_validates_code_postal(self):
        erp = Erp.objects.create(nom="x", code_postal="1234")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "code_postal" in excinfo.value.error_dict

    def test_clean_validates_commune_ext(self):
        commune = CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
        erp = Erp.objects.create(nom="x", code_postal="12345", voie="y", commune="missing")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "commune" in excinfo.value.error_dict

        erp = Erp.objects.create(nom="x", code_postal="34830", voie="y", commune="jacou")
        erp.clean()
        assert erp.commune_ext == commune

    def test_clean_validates_siret(self):
        CommuneFactory(nom="Jacou", code_postaux=["34830"], code_insee="34120", departement="34")
        erp = ErpFactory(siret="invalid siret", commune="Jacou")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "siret" in excinfo.value.error_dict

        erp.siret = "88076068100010"
        erp.clean()
        assert erp.siret == "88076068100010"

        erp.siret = "880 760 681 00010"
        erp.clean()
        assert erp.siret == "88076068100010"

    def test_clean_validates_voie(self):
        erp = Erp.objects.create(nom="x", code_postal="12345")
        with pytest.raises(ValidationError) as excinfo:
            erp.clean()
        assert "voie" in excinfo.value.error_dict
        assert "lieu_dit" in excinfo.value.error_dict

    def test_editable_by(self):
        owner = UserFactory()
        other_user = UserFactory()
        erp = ErpFactory(user=owner)
        assert erp.editable_by(owner) is True
        assert erp.editable_by(other_user) is False

    def test_metadata_tags_update_key(self):
        erp = Erp.objects.create(nom="erp1", metadata={"keepme": 42, "tags": ["foo", "bar"]})

        erp.metadata["tags"].append("plop")
        erp.save()

        erp = Erp.objects.get(metadata__tags__contains=["plop"])  # raises if not found
        assert erp.metadata["keepme"] == 42

    def test_metadata_tags_delete_key(self):
        erp = Erp.objects.create(nom="erp1", metadata={"keepme": 42, "tags": ["foo", "bar"]})

        del erp.metadata["keepme"]
        erp.save()

        erp = Erp.objects.get(metadata__tags__contains=["foo"])  # raises if not found
        assert "keepme" not in erp.metadata

    def test_metadata_tags_filter(self):
        Erp.objects.create(nom="erp1", metadata={"tags": ["foo", "bar"]})
        Erp.objects.create(nom="erp2", metadata={"tags": ["bar", "baz"]})

        assert Erp.objects.filter(metadata__tags__contains=["foo"]).count() == 1
        assert Erp.objects.filter(metadata__tags__contains=["baz"]).count() == 1
        assert Erp.objects.filter(metadata__tags__contains=["bar"]).count() == 2

    def test_metadata_update_nested_key(self):
        erp = Erp.objects.create(nom="erp1", metadata={"foo": {"bar": 42}})

        erp.metadata["foo"]["bar"] = 43
        erp.save()

        Erp.objects.get(metadata__foo__bar=43)  # raises if not found

    def test_save(self, activite):
        # test activity change, should wipe answers to conditional questions if we change the activity group
        hotel = Activite.objects.get(nom="Hôtel")
        erp = ErpFactory(activite=hotel, accessibilite__accueil_chambre_nombre_accessibles=1)
        assert erp.activite.groups.first().name == "Hébergement", "Conditions for test not met"

        access = erp.accessibilite
        access.accueil_chambre_numero_visible = True
        access.save()

        erp = Erp.objects.get(pk=erp.pk)
        erp.activite = Activite.objects.get(nom="Hôtel restaurant")
        erp.save()

        erp = Erp.objects.get(pk=erp.pk)
        access = erp.accessibilite
        assert (
            access.accueil_chambre_numero_visible is True
        ), "should not wipe conditional questions' answers, same group"
        assert erp.activite.nom == "Hôtel restaurant"

        erp.activite = Activite.objects.get(nom="Accessoires")
        erp.save()

        erp = Erp.objects.get(pk=erp.pk)

        access = erp.accessibilite
        assert access.accueil_chambre_numero_visible is None, "should wipe conditional questions' answers"
        assert erp.activite.nom == "Accessoires"

        assert erp.published
        erp.permanently_closed = True
        erp.save()

        erp.refresh_from_db()
        assert erp.published is False, "ERP should have been unpublished as it is flagged permanently closed"

    @pytest.mark.django_db
    def test_get_absolute_url(self):
        commune = CommuneFactory(departement="974", nom="Saint Paul")
        erp = ErpFactory(commune_ext=commune)
        assert "974-saint-paul" in erp.get_absolute_url()

        commune = CommuneFactory(departement="2B", nom="Calenzana")
        erp = ErpFactory(commune_ext=commune)
        assert "2b-calenzana" in erp.get_absolute_url()


@pytest.mark.django_db
class TestActivitySuggestion:
    def test_save(self, mocker):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
        mock_mail_admins = mocker.patch("core.mailer.BrevoMailer.mail_admins", return_value=True)

        niko = UserFactory()
        sophie = UserFactory()

        ActiviteFactory(slug="autre", nom="Autre")
        boulangerie = ActiviteFactory(nom="Boulangerie")
        erp = ErpFactory(activite=boulangerie)
        activity_suggest = ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp)
        activity_suggest.mapped_activity = Activite.objects.create(nom="Bisounours")
        activity_suggest.save()

        erp.refresh_from_db()
        erp.activite.refresh_from_db()

        assert erp.activite.nom == "Boulangerie", "ERP should not be affected as it was not in Other activity."

        erp.activite = Activite.objects.get(slug="autre")
        erp.save()
        activity_suggest = ActivitySuggestion.objects.create(name="Vendeur de rêves2", erp=erp)

        erp.refresh_from_db()
        erp.activite.refresh_from_db()
        assert erp.activite.nom == "Autre", "ERP should not be affected as there is not new mapped activity."

        activity_suggest.mapped_activity = Activite.objects.create(nom="Bisounours2")
        activity_suggest.save()
        assert (
            erp.activite.nom == "Bisounours2"
        ), "ERP should be impacted as it was in Other activity with a new mapped activity"

        mock_mail.assert_not_called()

        # spamming suggestions
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp, user=niko)
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp, user=niko)
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp, user=sophie)
        mock_mail.assert_not_called()

        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp, user=niko)
        mock_mail.assert_called_once_with(
            to_list=niko.email, template="spam_activities_suggestion", context={"nb_times": 3}
        )
        mock_mail_admins.assert_called_once_with(
            template="spam_activities_suggestion_admin",
            context={"nb_times": 3, "username": niko.username, "email": niko.email},
        )
        ActivitySuggestion.objects.create(name="Vendeur de rêves", erp=erp, user=niko)
        assert mock_mail.call_count == 2
        assert mock_mail_admins.call_count == 2


@pytest.mark.django_db
def test_get_global_timestamps_no_history():
    erp = ErpFactory()
    global_timestamps = erp.get_global_timestamps()
    assert global_timestamps["created_at"] == global_timestamps["updated_at"]


@pytest.mark.django_db
def test_get_global_timestamps_with_history(django_assert_num_queries):
    erp = ErpFactory(with_accessibilite=True)
    user = UserFactory()

    with reversion.create_revision():
        reversion.set_user(user)
        accessibilite = erp.accessibilite
        accessibilite.sanitaires_presence = False
        accessibilite.sanitaires_adaptes = None
        accessibilite.transport_station_presence = True
        accessibilite.save()

    with reversion.create_revision():
        reversion.set_user(user)
        accessibilite = erp.accessibilite
        accessibilite.sanitaires_presence = True
        accessibilite.sanitaires_adaptes = None
        accessibilite.transport_station_presence = False
        accessibilite.save()

    with django_assert_num_queries(1):
        global_timestamps = erp.get_global_timestamps()
    assert global_timestamps["updated_at"] > global_timestamps["created_at"]


@pytest.mark.django_db
def test_merge_take_value_from_b_object():
    a_access = AccessibiliteFactory(stationnement_presence=None)
    b_access = AccessibiliteFactory(stationnement_presence=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is True


@pytest.mark.django_db
def test_merge_does_not_take_nullable_value_from_b_object():
    a_access = AccessibiliteFactory(stationnement_presence=True)
    b_access = AccessibiliteFactory(stationnement_presence=None)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is True


@pytest.mark.django_db
def test_merge_respects_parent_child_consistency():
    a_access = AccessibiliteFactory(stationnement_presence=None, stationnement_pmr=None)
    b_access = AccessibiliteFactory(stationnement_presence=True, stationnement_pmr=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    with pytest.raises(IntegrityError):
        a_erp.merge_accessibility_with(b_erp, fields=["stationnement_pmr"])


@pytest.mark.django_db
def test_merge_respects_fields():
    a_access = AccessibiliteFactory(stationnement_presence=True, stationnement_pmr=None)
    b_access = AccessibiliteFactory(stationnement_presence=True, stationnement_pmr=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    a_erp.merge_accessibility_with(b_erp, fields=["stationnement_pmr"])

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is True
    assert a_erp.accessibilite.stationnement_pmr is True


@pytest.mark.django_db
def test_merge_cant_handle_conflicting_values():
    a_access = AccessibiliteFactory(stationnement_presence=False)
    b_access = AccessibiliteFactory(stationnement_presence=True)

    a_erp = a_access.erp
    b_erp = b_access.erp
    with pytest.raises(MergeException):
        a_erp.merge_accessibility_with(b_erp)

    a_erp.refresh_from_db()
    assert a_erp.accessibilite.stationnement_presence is False


@pytest.mark.django_db
def test_get_outside_steps_direction_text():
    access = AccessibiliteFactory(
        cheminement_ext_presence=True,
        cheminement_ext_plain_pied=False,
        cheminement_ext_nombre_marches=10,
        cheminement_ext_sens_marches="montant",
    )

    assert access.get_outside_steps_direction_text() == "montantes"

    access.cheminement_ext_nombre_marches = 1
    access.save()
    assert access.get_outside_steps_direction_text() == "montante"

    access.cheminement_ext_nombre_marches = None
    access.save()
    assert access.get_outside_steps_direction_text() == "montantes"

    access.cheminement_ext_nombre_marches = 0
    access.save()
    assert access.get_outside_steps_direction_text() == "montantes"
