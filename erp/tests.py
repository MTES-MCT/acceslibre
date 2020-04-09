import pytest

from django.contrib.gis.geos import Point
from unittest import mock

from .forms import AdminErpForm, ViewAccessibiliteForm

VALID_ADDRESS = {
    "nom": "plop",
    "numero": "4",
    "voie": "rue de la paix",
    "lieu_dit": "blah",
    "code_postal": "75000",
    "commune": "Paris",
}
INVALID_ADDRESS = {
    "nom": "plop",
    "voie": "invalid",
    "code_postal": "XXXXX",
    "commune": "invalid",
}
POINT = Point((0, 0))


# AdminErpForm


@pytest.fixture
def fake_geocoder():
    return lambda _: {
        "geom": POINT,
        "numero": "4",
        "voie": "Rue de la Paix",
        "lieu_dit": None,
        "code_postal": "75002",
        "commune": "Paris",
        "code_insee": "75111",
    }


def test_AdminErpForm_get_adresse(fake_geocoder):
    form = AdminErpForm(VALID_ADDRESS, geocode=fake_geocoder,)
    form.is_valid()  # populates cleaned_data
    assert form.get_adresse() == "4 Rue de la Paix 75002 Paris"


def test_AdminErpForm_geocode_adresse(fake_geocoder):
    form = AdminErpForm(VALID_ADDRESS, geocode=fake_geocoder,)
    form.is_valid()
    assert form.cleaned_data["geom"] == POINT
    assert form.cleaned_data["numero"] == "4"
    assert form.cleaned_data["voie"] == "Rue de la Paix"
    assert form.cleaned_data["lieu_dit"] == None
    assert form.cleaned_data["code_postal"] == "75002"
    assert form.cleaned_data["commune"] == "Paris"
    assert form.cleaned_data["code_insee"] == "75111"


def test_AdminErpForm_invalid_on_empty_geocode_results():
    form = AdminErpForm(INVALID_ADDRESS, geocode=lambda _: None,)
    assert form.is_valid() == False


def test_AdminErpForm_valid_on_geocoded_results(fake_geocoder):
    form = AdminErpForm(VALID_ADDRESS, geocode=fake_geocoder,)
    assert form.is_valid() == True


# ViewAccessibiliteForm


def test_ViewAccessibiliteForm_get_accessibilite_data():
    form = ViewAccessibiliteForm()
    data = form.get_accessibilite_data()
    assert list(data.keys()) == [
        "Entrée",
        "Stationnement",
        "Cheminement extérieur",
        "Accueil",
        "Sanitaires",
        "Commentaire",
    ]
