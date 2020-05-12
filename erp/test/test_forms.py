import pytest

from django.contrib.gis.geos import Point
from unittest import mock

from ..forms import AdminAccessibiliteForm, AdminErpForm, ViewAccessibiliteForm
from ..models import Commune


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


@pytest.fixture
def paris_commune():
    c = Commune(nom="Paris", departement="75", code_insee="75111", geom=POINT)
    c.save()


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


@pytest.mark.django_db
def test_AdminErpForm_get_adresse(fake_geocoder, paris_commune):
    form = AdminErpForm(VALID_ADDRESS, geocode=fake_geocoder,)
    form.is_valid()  # populates cleaned_data
    assert form.get_adresse() == "4 Rue de la Paix 75002 Paris"


@pytest.mark.django_db
def test_AdminErpForm_geocode_adresse(fake_geocoder, paris_commune):
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


@pytest.mark.django_db
def test_AdminErpForm_valid_on_geocoded_results(fake_geocoder, paris_commune):
    form = AdminErpForm(VALID_ADDRESS, geocode=fake_geocoder,)
    assert form.is_valid() == True


# ViewAccessibiliteForm


def test_ViewAccessibiliteForm_empty():
    form = ViewAccessibiliteForm()
    data = form.get_accessibilite_data()
    assert list(data.keys()) == []


def test_ViewAccessibiliteForm_filled():
    form = ViewAccessibiliteForm(
        {
            "entree_reperage": True,
            "transport_station_presence": True,
            "stationnement_presence": True,
            "cheminement_ext_presence": True,
            "accueil_visibilite": True,
            "sanitaires_presence": True,
            "commentaire": "plop",
        }
    )
    data = form.get_accessibilite_data()
    assert list(data.keys()) == [
        "Transport en commun",
        "Stationnement",
        "Espace et cheminement extérieur",
        "Entrée",
        "Accueil",
        "Sanitaires",
        "Commentaire",
    ]


def test_ViewAccessibiliteForm_filled_null_comment():
    form = ViewAccessibiliteForm({"sanitaires_presence": True, "commentaire": "",})
    data = form.get_accessibilite_data()
    assert list(data.keys()) == ["Sanitaires"]


def test_ViewAccessibiliteForm_serialized():
    form = ViewAccessibiliteForm({"entree_reperage": True,})
    data = form.get_accessibilite_data()
    expected = {
        "template_name": "django/forms/widgets/select.html",
        "name": "entree_reperage",
        "label": "Entrée facilement repérable",
        "help_text": "Y a-t-il des éléments de repérage de l'entrée (numéro de rue à proximité, enseigne, etc)",
        "value": True,
        "warning": False,
    }
    assert expected in data["Entrée"]["fields"]
