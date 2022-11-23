import pytest

from django.contrib.gis.geos import Point

from erp import forms
from erp.models import Commune, Erp
from erp.provider import geocoder


POINT = Point((0, 0))


@pytest.fixture
def form_data(data):
    return {
        "source": "sirene",
        "source_id": "xxx",
        "user": data.niko,
        "user_type": "public",
        "nom": "plop",
        "numero": "4",
        "voie": "rue de la paix",
        "lieu_dit": "blah",
        "code_postal": "75002",
        "commune": "Paris",
        "lat": 43.657028,
        "lon": 2.6754,
        "asp_id": 1234,
    }


@pytest.fixture
def geocoder_result_ok():
    return {
        "geom": POINT,
        "numero": "4",
        "voie": "Rue de la Paix",
        "lieu_dit": None,
        "code_postal": "75002",
        "commune": "Paris",
        "code_insee": "75111",
    }


@pytest.fixture
def paris_commune():
    c = Commune(nom="Paris", departement="75", code_insee="75111", geom=POINT)
    c.save()


@pytest.mark.django_db
def test_BaseErpForm_get_adresse_query(
    form_data, mocker, geocoder_result_ok, paris_commune
):
    mocker.patch("erp.provider.geocoder.geocode", return_value=geocoder_result_ok)
    form = forms.AdminErpForm(form_data)
    form.is_valid()  # populates cleaned_data
    assert form.get_adresse_query() == "4 Rue de la Paix, Paris"


@pytest.mark.django_db
def test_BaseErpForm_geocode_adresse(
    form_data, mocker, geocoder_result_ok, paris_commune
):
    mocker.patch("erp.provider.geocoder.geocode", return_value=geocoder_result_ok)
    form = forms.AdminErpForm(form_data)
    form.is_valid()
    assert form.cleaned_data["geom"] == POINT
    assert form.cleaned_data["numero"] == "4"
    assert form.cleaned_data["voie"] == "Rue de la Paix"
    assert form.cleaned_data["lieu_dit"] is None
    assert form.cleaned_data["code_postal"] == "75002"
    assert form.cleaned_data["commune"] == "Paris"
    assert form.cleaned_data["code_insee"] == "75111"


@pytest.mark.django_db
def test_BaseErpForm_clean_geom_missing(data, mocker):
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value={
            "geom": None,
            "numero": None,
            "voie": "Grand rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34120",
        },
    )
    form = forms.PublicErpEditInfosForm(
        {
            "source": "sirene",
            "source_id": "xxx",
            "user": data.niko,
            "user_type": "public",
            "activite": str(data.boulangerie.pk),
            "nom": "test erp",
            "numero": "4",
            "voie": "Grand rue",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "Jacou",
            "lat": 43.657028,
            "lon": 2.6754,
        }
    )
    assert form.is_valid() is False
    assert "voie" in form.errors
    assert "Adresse non localisable" in form.errors["voie"][0]


@pytest.mark.django_db
def test_BaseErpForm_clean_code_postal_mismatch(data, mocker):
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value={
            "geom": POINT,
            "numero": None,
            "voie": "Grand rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "34120",
        },
    )
    form = forms.PublicErpEditInfosForm(
        {
            "source": "sirene",
            "source_id": "xxx",
            "user": data.niko,
            "user_type": "public",
            "activite": str(data.boulangerie.pk),
            "nom": "plop",
            "numero": "4",
            "voie": "rue de la paix",
            "lieu_dit": "",
            "code_postal": "75002",
            "commune": "Paris",
            "lat": 44.657028,
            "lon": 2.6754,
        }
    )
    assert form.is_valid() is False
    assert "code_postal" in form.errors
    assert "pas localisable au code postal 75002" in form.errors["code_postal"][0]


@pytest.mark.django_db
def test_BaseErpForm_clean_numero_mismatch(data, mocker):
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value={
            "geom": POINT,
            "numero": None,
            "voie": "Grand rue",
            "lieu_dit": None,
            "code_postal": "34830",
            "commune": "Jacou",
            "code_insee": "12345",
        },
    )
    form = forms.PublicErpEditInfosForm(
        {
            "source": "sirene",
            "source_id": "xxx",
            "user": data.niko,
            "user_type": "public",
            "activite": str(data.boulangerie.pk),
            "nom": "test erp",
            "numero": "4",
            "voie": "Grand rue",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "Jacou",
            "lat": 43.657028,
            "lon": 2.6754,
        }
    )
    assert form.is_valid() is True
    assert "numero" not in form.errors
    assert form.cleaned_data["numero"] == "4"
    form.save()
    Erp.objects.get(slug="test-erp").numero == "4"


def test_BaseErpForm_invalid_on_empty_geocode_results(form_data, mocker):
    mocker.patch("erp.provider.geocoder.geocode", return_value=None)
    form = forms.AdminErpForm(form_data)
    assert form.is_valid() is False


@pytest.mark.django_db
def test_BaseErpForm_valid_on_geocoded_results(
    form_data, mocker, geocoder_result_ok, paris_commune
):
    mocker.patch("erp.provider.geocoder.geocode", return_value=geocoder_result_ok)
    form = forms.AdminErpForm(form_data)
    assert form.is_valid() is True


def test_BaseErpForm_retrieve_code_insee_from_manual_input(data):
    form = forms.PublicErpAdminInfosForm(
        {
            "source": Erp.SOURCE_PUBLIC,
            "source_id": "",
            "geom": None,
            "nom": "xxx jacou",
            "activite": data.boulangerie.pk,
            "numero": "12",
            "voie": "grand rue",
            "lieu_dit": "",
            "code_postal": "34830",
            "commune": "jacou",
            "contact_email": "",
            "site_internet": "",
            "telephone": "",
            "lat": 43.657028,
            "lon": 2.6754,
        }
    )
    assert form.is_valid() is True
    assert form.cleaned_data["geom"] == Point(2.6754, 43.657028, srid=4326), "geom should have by built from lat & lon"
