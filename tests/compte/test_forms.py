import pytest

from compte import forms


@pytest.mark.django_db
def test_CustomRegistrationForm():
    form = forms.CustomRegistrationForm()
    assert form.is_valid() is False

    form = forms.CustomRegistrationForm({"username": "toto@toto.com"})
    assert form.is_valid() is False
    assert forms.USERNAME_RULES in form.errors["username"]

    form = forms.CustomRegistrationForm({"username": "toto+toto"})
    assert form.is_valid() is False
    assert forms.USERNAME_RULES in form.errors["username"]

    form = forms.CustomRegistrationForm(
        {"username": "".join(map(lambda _: "x", range(0, 33)))}
    )  # 33c length string
    assert form.is_valid() is False
    assert (
        "Assurez-vous que cette valeur comporte au plus 32 caractères (actuellement 33)."
        in form.errors["username"]
    )

    form = forms.CustomRegistrationForm({"username": "jean-pierre.timbault_42"})
    assert "username" not in form.errors
