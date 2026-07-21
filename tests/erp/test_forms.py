import pytest

from erp import forms, schema
from erp.models import ACTIVITY_GROUPS
from tests.factories import (
    AccessibiliteFactory,
    ActiviteFactory,
    ActivitiesGroupFactory,
    CommuneFactory,
    ErpFactory,
)


@pytest.mark.django_db
def test_AdminAccessibiliteForm_sanitaires_adaptes_value_mapping():
    erp = ErpFactory(accessibilite__sanitaires_presence=True, accessibilite__sanitaires_adaptes=True)

    form = forms.AdminAccessibiliteForm(instance=erp.accessibilite)

    assert form.initial["sanitaires_adaptes"] is True


def test_ContribAccessibiliteHealthcareForm_clears_soignant_experience_when_soignant_false():
    form = forms.ContribAccessibiliteHealthcareForm()
    form.cleaned_data = {
        "accueil_soignant": False,
        "accueil_soignant_experience": [
            schema.ACCUEIL_SOIGNANT_EXPERIENCE_VISUEL,
            schema.ACCUEIL_SOIGNANT_EXPERIENCE_AUDITIF,
        ],
    }

    assert form.clean_accueil_soignant_experience() is None


def test_ContribAccessibiliteHealthcareForm_keeps_soignant_experience_when_soignant_true():
    form = forms.ContribAccessibiliteHealthcareForm()
    experiences = [
        schema.ACCUEIL_SOIGNANT_EXPERIENCE_VISUEL,
        schema.ACCUEIL_SOIGNANT_EXPERIENCE_MOTEUR,
    ]
    form.cleaned_data = {
        "accueil_soignant": True,
        "accueil_soignant_experience": experiences,
    }

    assert form.clean_accueil_soignant_experience() == experiences


@pytest.mark.django_db
def test_ProviderGlobalSearchForm():
    commune = CommuneFactory(nom="Jacou", code_insee="34120", departement="34")
    form = forms.ProviderGlobalSearchForm(initial={"code": commune.code_insee})

    assert form.initial["commune_search"] == "Jacou (34 - Hérault)"
    assert form.initial["code_insee"] == commune.code_insee


def _combined_form_for(access, section):
    return forms.CombinedAccessibiliteForm(
        forms.get_contrib_forms_for_activity(access.erp.activite),
        schema.get_section_fields(section),
        instance=access,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "section,field",
    (
        (schema.SECTION_ACCUEIL, "accueil_signaletique_interieure"),
        (schema.SECTION_CHEMINEMENT_EXT, "cheminement_ext_signaletique_exterieure"),
    ),
)
def test_sports_equipment_form_keeps_whitelisted_large_establishments_fields(section, field):
    activity = ActiviteFactory(slug="gymnase", nom="Gymnase")

    ActivitiesGroupFactory(activities=[activity], name=ACTIVITY_GROUPS["SPORTS_EQUIPMENT"])

    access = AccessibiliteFactory(erp=ErpFactory(activite=activity))
    form = _combined_form_for(access, section)

    assert field in form.fields
    assert form.fields[field].label == schema.get_label(field)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "section,field",
    (
        (schema.SECTION_ACCUEIL, "accueil_signaletique_interieure"),
        (schema.SECTION_CHEMINEMENT_EXT, "cheminement_ext_signaletique_exterieure"),
    ),
)
def test_school_form_excludes_non_whitelisted_large_establishments_fields(section, field):
    activity = ActiviteFactory(slug="ecole", nom="École")
    ActivitiesGroupFactory(activities=[activity], name=ACTIVITY_GROUPS["SCHOOL"])
    access = AccessibiliteFactory(erp=ErpFactory(activite=activity))
    form = _combined_form_for(access, section)

    assert field not in form.fields


@pytest.mark.django_db
def test_school_form_keeps_whitelisted_large_establishments_fields():
    activity = ActiviteFactory(slug="ecole", nom="École")
    ActivitiesGroupFactory(activities=[activity], name=ACTIVITY_GROUPS["SCHOOL"])
    access = AccessibiliteFactory(erp=ErpFactory(activite=activity))
    form = _combined_form_for(access, schema.SECTION_ACCUEIL)

    for field in forms.ContribAccessibiliteSchoolsForm.large_establishments_fields_to_keep:
        assert field in form.fields
        assert form.fields[field].label == schema.get_label(field)
