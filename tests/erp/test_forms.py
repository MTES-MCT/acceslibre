import pytest

from erp import forms
from auth import forms as auth_forms


@pytest.mark.django_db
def test_CustomRegistrationForm():
    form = auth_forms.CustomRegistrationForm()
    assert form.is_valid() is False

    form = auth_forms.CustomRegistrationForm({"username": "toto@toto.com"})
    assert form.is_valid() is False
    assert auth_forms.USERNAME_RULES in form.errors["username"]

    form = auth_forms.CustomRegistrationForm({"username": "toto+toto"})
    assert form.is_valid() is False
    assert auth_forms.USERNAME_RULES in form.errors["username"]

    form = auth_forms.CustomRegistrationForm(
        {"username": "".join(map(lambda _: "x", range(0, 33)))}
    )  # 33c length string
    assert form.is_valid() is False
    assert (
        "Assurez-vous que cette valeur comporte au plus 32 caractères (actuellement 33)."
        in form.errors["username"]
    )

    form = auth_forms.CustomRegistrationForm({"username": "jean-pierre.timbault_42"})
    assert "username" not in form.errors


def test_AdminAccessibiliteForm_sanitaires_adaptes_value_mapping(data):
    data.accessibilite.sanitaires_adaptes = 12
    data.accessibilite.save()

    form = forms.AdminAccessibiliteForm(instance=data.accessibilite)

    assert form.initial["sanitaires_adaptes"] == 1


# ProviderGlobalSearchForm


def test_ProviderGlobalSearchForm(data):
    form = forms.ProviderGlobalSearchForm(initial={"code_insee": data.jacou.code_insee})

    assert form.initial["commune_search"] == "Jacou (34 - Hérault)"
