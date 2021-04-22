import pytest

from erp import schema


def test_get_api_fieldsets():
    fieldsets = schema.get_api_fieldsets()
    assert type(fieldsets) == dict

    for (_, section) in fieldsets.items():
        assert "label" in section
        assert "fields" in section
        assert type(section["fields"]) == list


def test_get_admin_fieldsets():
    fieldsets = schema.get_admin_fieldsets()
    assert type(fieldsets) == list

    for (section_label, section) in fieldsets:
        assert type(section) == dict
        assert "description" in section
        assert "fields" in section
        assert type(section["fields"]) == list


def test_get_form_fieldsets():
    fieldsets = schema.get_form_fieldsets()
    assert type(fieldsets) == dict

    for (_, section) in fieldsets.items():
        assert type(section) == dict
        assert "icon" in section
        assert "tabid" in section
        assert "description" in section
        assert "fields" in section
        assert type(section["fields"]) == list
        for field in section["fields"]:
            assert "id" in field
            assert "warn_if" in field


def test_get_labels():
    result = schema.get_labels()
    assert type(result) == dict


def test_get_label():
    result = schema.get_label("cheminement_ext_rampe")
    assert result == "Rampe"

    result = schema.get_label("invalid", "yolo")
    assert result == "yolo"


def test_get_help_texts():
    result = schema.get_help_texts()
    assert type(result) == dict


def test_get_help_text():
    result = schema.get_help_text("cheminement_ext_rampe")
    assert (
        result
        == "S'il existe une rampe ayant une pente douce, est-elle fixe ou amovible&nbsp;?"
    )

    result = schema.get_help_text("invalid", "yolo")
    assert result == "yolo"


def test_get_section_fields():
    result = schema.get_section_fields(schema.SECTION_ENTREE)
    assert type(result) == list
    assert "entree_reperage" in result
    assert "cheminement_ext_pente" not in result


def test_get_nullable_bool_fields():
    result = schema.get_nullable_bool_fields()
    assert type(result) == list
