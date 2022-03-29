import pytest

from erp import forms


def test_AdminAccessibiliteForm_sanitaires_adaptes_value_mapping(data):
    data.accessibilite.sanitaires_adaptes = True
    data.accessibilite.save()

    form = forms.AdminAccessibiliteForm(instance=data.accessibilite)

    assert form.initial["sanitaires_adaptes"] is True


def test_ProviderGlobalSearchForm(data):
    form = forms.ProviderGlobalSearchForm(initial={"code": data.jacou.code_insee})

    assert form.initial["commune_search"] == "Jacou (34 - Hérault)"
    assert form.initial["code_insee"] == data.jacou.code_insee
