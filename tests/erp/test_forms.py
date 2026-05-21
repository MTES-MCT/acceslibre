import pytest

from erp import forms, schema
from tests.factories import CommuneFactory, ErpFactory


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
