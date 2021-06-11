import pytest


from erp import schema
from erp import forms
from erp.models import Accessibilite
from erp.schema import get_help_text_ui, get_help_text_ui_neg


@pytest.fixture
def form_test():
    def _factory(name, value):
        instance = Accessibilite(**{name: value})
        form = forms.ViewAccessibiliteForm(instance=instance)
        return form.get_accessibilite_data(flatten=True)

    return _factory


def test_ViewAccessibiliteForm_empty():
    form = forms.ViewAccessibiliteForm()
    data = form.get_accessibilite_data()
    assert list(data.keys()) == []


def test_ViewAccessibiliteForm_filled():
    form = forms.ViewAccessibiliteForm(
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
        "Transports en commun",
        "Stationnement",
        "Chemin extérieur",
        "Entrée",
        "Accueil",
        "Sanitaires",
        "Commentaire",
    ]


def test_ViewAccessibiliteForm_filled_with_comment():
    form = forms.ViewAccessibiliteForm({"commentaire": "plop"})
    data = form.get_accessibilite_data()
    field = data["Commentaire"]["fields"][0]
    assert field["value"] == "plop"
    assert field["is_comment"] is True


def test_ViewAccessibiliteForm_filled_null_comment():
    form = forms.ViewAccessibiliteForm(
        {
            "sanitaires_presence": True,
            "commentaire": "",
        }
    )
    data = form.get_accessibilite_data()
    assert list(data.keys()) == ["Sanitaires"]


def test_ViewAccessibiliteForm_serialized():
    form = forms.ViewAccessibiliteForm(
        {
            "entree_reperage": True,
        }
    )
    data = form.get_accessibilite_data()
    field = data["Entrée"]["fields"][0]

    assert field["name"] == "entree_reperage"
    assert field["label"] == schema.get_help_text_ui("entree_reperage")
    assert field["value"] is True
    assert field["warning"] is False
    assert field["is_comment"] is False


def test_ViewAccessibiliteForm_labels(form_test):
    def assert_absence(name, value):
        assert get_help_text_ui_neg(name) in [
            f["label"] for f in form_test(name, value)
        ]

    def assert_presence(name, value):
        assert get_help_text_ui(name) in [f["label"] for f in form_test(name, value)]

    def assert_missing(name, value):
        assert get_help_text_ui(name) not in [
            f["label"] for f in form_test(name, value)
        ]
        assert get_help_text_ui_neg(name) not in [
            f["label"] for f in form_test(name, value)
        ]

    # boolean fields
    assert_presence("sanitaires_presence", True)
    assert_absence("sanitaires_presence", False)
    assert_missing("sanitaires_presence", None)

    # integer fields
    assert_presence("sanitaires_adaptes", 1)
    assert_presence("sanitaires_adaptes", 2)
    assert_absence("sanitaires_adaptes", 0)
    assert_missing("sanitaires_adaptes", None)

    # single string fields
    assert_presence("cheminement_ext_pente_degre_difficulte", schema.PENTE_LEGERE)
    assert_missing("cheminement_ext_pente_degre_difficulte", None)

    # multiple strings fields
    assert_presence(
        "entree_dispositif_appel_type",
        [schema.DISPOSITIFS_APPEL_BOUTON, schema.DISPOSITIFS_APPEL_INTERPHONE],
    )
    assert_missing("entree_dispositif_appel_type", [])
    assert_missing("entree_dispositif_appel_type", None)

    # special cases
    assert_presence("cheminement_ext_devers", schema.DEVERS_LEGER)
    assert_absence("cheminement_ext_devers", schema.DEVERS_AUCUN)
    assert_missing("cheminement_ext_devers", None)

    for f in [
        "cheminement_ext_rampe",
        "entree_marches_rampe",
        "accueil_cheminement_rampe",
    ]:
        assert_presence(f, schema.RAMPE_AMOVIBLE)
        assert_absence(f, schema.RAMPE_AUCUNE)
        assert_missing(f, None)

    assert_presence("accueil_personnels", schema.PERSONNELS_FORMES)
    assert_absence("accueil_personnels", schema.PERSONNELS_AUCUN)
    assert_missing("accueil_personnels", None)
