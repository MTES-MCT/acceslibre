import pytest

from erp import forms
from tests.factories import CommuneFactory, ErpFactory


@pytest.mark.django_db
def test_AdminAccessibiliteForm_sanitaires_adaptes_value_mapping():
    erp = ErpFactory(accessibilite__sanitaires_presence=True, accessibilite__sanitaires_adaptes=True)

    form = forms.AdminAccessibiliteForm(instance=erp.accessibilite)

    assert form.initial["sanitaires_adaptes"] is True


@pytest.mark.django_db
def test_ProviderGlobalSearchForm():
    commune = CommuneFactory(nom="Jacou", code_insee="34120", departement="34")
    form = forms.ProviderGlobalSearchForm(initial={"code": commune.code_insee})

    assert form.initial["commune_search"] == "Jacou (34 - Hérault)"
    assert form.initial["code_insee"] == commune.code_insee
