import pytest

from erp import schema


def test_get_api_fieldsets():
    fieldsets = schema.get_api_fieldsets()
    assert isinstance(fieldsets, dict)

    for _, section in fieldsets.items():
        assert "label" in section
        assert "fields" in section
        assert isinstance(section["fields"], list)


def test_get_admin_fieldsets():
    fieldsets = schema.get_admin_fieldsets()
    assert isinstance(fieldsets, list)

    for section_label, section in fieldsets:
        assert isinstance(section, dict)
        assert "description" in section
        assert "fields" in section
        assert isinstance(section["fields"], list)


def test_get_form_fieldsets():
    fieldsets = schema.get_form_fieldsets()
    assert isinstance(fieldsets, dict)

    for _, section in fieldsets.items():
        assert isinstance(section, dict)
        assert "icon" in section
        assert "tabid" in section
        assert "description" in section
        assert "fields" in section
        assert isinstance(section["fields"], list)
        for field in section["fields"]:
            assert "id" in field
            assert "warn_if" in field


def test_get_labels():
    result = schema.get_labels()
    assert isinstance(result, dict)


def test_get_label():
    result = schema.get_label("cheminement_ext_rampe")
    assert result == "Rampe"

    result = schema.get_label("invalid", "yolo")
    assert result == "yolo"


def test_get_help_texts():
    result = schema.get_help_texts()
    assert isinstance(result, dict)


def test_get_help_text():
    result = schema.get_help_text("cheminement_ext_rampe")
    assert result == "S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?"

    result = schema.get_help_text("invalid", "yolo")
    assert result == "yolo"


@pytest.mark.parametrize(
    "field, value, expected",
    [
        ("sanitaires_presence", True, "Oui"),
        ("sanitaires_presence", False, "Non"),
        ("sanitaires_presence", None, "Inconnu"),
        ("accueil_cheminement_nombre_marches", 1, "1"),
        ("accueil_cheminement_nombre_marches", 0, "0"),
        ("cheminement_ext_devers", "important", "Important"),
        ("labels", ["dpt", "th"], "Destination pour Tous, Tourisme & Handicap"),
        ("labels", [], "Vide"),
    ],
)
def test_get_human_readable_value_ok(field, value, expected):
    assert schema.get_human_readable_value(field, value) == expected


def test_get_human_readable_value_ko():
    with pytest.raises(NotImplementedError):
        schema.get_human_readable_value("sanitaires_presence", {})


def test_get_section_fields():
    result = schema.get_section_fields(schema.SECTION_ENTREE)
    assert isinstance(result, list)
    assert "entree_reperage" in result
    assert "cheminement_ext_pente_presence" not in result


def test_get_nullable_bool_fields():
    result = schema.get_nullable_bool_fields()
    assert isinstance(result, list)


@pytest.mark.parametrize(
    "field, expected",
    [
        ("sanitaires_presence", "boolean"),
        ("accueil_cheminement_nombre_marches", "number"),
        ("cheminement_ext_devers", "string"),
        ("labels", "array"),
    ],
)
def test_get_type(field, expected):
    assert schema.get_type(field) == expected
