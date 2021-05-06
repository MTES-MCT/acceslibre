from pathlib import Path
from typing import Any

from frictionless import Schema, Field

from erp import schema
from erp.export.models import ETALAB_SCHEMA_FIELDS
from erp.schema import FIELDS

TRUE_VALUES = [
    "true",
    "True",
    "TRUE",
    "1",
    "vrai",
    "Vrai",
    "VRAI",
    "oui",
    "Oui",
    "OUI",
]
FALSE_VALUES = [
    "false",
    "False",
    "FALSE",
    "0",
    "faux",
    "Faux",
    "FAUX",
    "non",
    "Non",
    "NON",
]


def generate_schema(
    base="static/base-schema.json",
    outfile="static/schema.json",
    repository="",
):
    table_schema = Schema(base)
    table_schema["path"] = repository + "schema.json"
    table_schema.get("resources")[0]["path"] = repository + "exemple-valide.csv"

    # table_schema["version"] = "0.0.1"

    for field_name in ETALAB_SCHEMA_FIELDS:
        f = FIELDS.get(field_name)
        if not f:
            continue

        table_schema.add_field(create_field(field_name, f))

    table_schema.to_json(outfile)


def create_field(field_name, field):
    constraints = get_constraints(field_name, field)
    schema_field = Field(
        name=field_name,
        type=map_types(field.get("type")),
        description=field.get("help_text_ui") or field.get("description"),
        title=field.get("label"),
        true_values=constraints.get("boolTrue", None),
        false_values=constraints.get("boolFalse", None),
        constraints=constraints.get("enum", None),
        array_item=constraints.get("arrayItem", None),
    )

    schema_field["example"] = field.get(
        "example", generate_example_text(field_name, field)
    ) or generate_example_text(field_name, field)

    return schema_field


def map_types(from_format):
    if from_format == "number":
        return "integer"
    return from_format


def get_constraints(field_name: str, field: Any) -> dict:
    """
    Get TableSchema constraints. The key will be identified when constructing fields to avoid another conditional
    """
    constraints = {}
    enum = get_linked_enum(field_name)
    field_type = map_types(field.get("type"))
    if enum and field_type == "string":
        constraints["enum"] = {}

        constraints["enum"]["enum"] = [
            value[0] for value in enum if value[0] is not None
        ]
    elif enum and field_type == "array":
        constraints["arrayItem"] = {}
        constraints["arrayItem"]["type"] = "string"
        constraints["arrayItem"]["enum"] = [
            value[0] for value in enum if value[0] is not None
        ]
    elif field_type == "boolean":
        constraints["boolTrue"] = TRUE_VALUES
        constraints["boolFalse"] = FALSE_VALUES

    return constraints


def get_linked_enum(field_name):
    if field_name == "cheminement_ext_devers":
        return schema.DEVERS_CHOICES
    if field_name == "entree_marches_rampe":
        return schema.RAMPE_CHOICES
    if field_name == "entree_marches_sens":
        return schema.ESCALIER_SENS
    if field_name == "entree_dispositif_appel_type":
        return schema.DISPOSITIFS_APPEL_CHOICES
    if field_name == "accueil_personnels":
        return schema.PERSONNELS_CHOICES
    if field_name == "accueil_equipements_malentendants":
        return schema.EQUIPEMENT_MALENTENDANT_CHOICES
    if field_name == "accueil_cheminement_sens_marches":
        return schema.ESCALIER_SENS
    if field_name == "accueil_cheminement_rampe":
        return schema.RAMPE_CHOICES
    if field_name == "cheminement_ext_sens_marches":
        return schema.ESCALIER_SENS
    if field_name == "cheminement_ext_pente_degre_difficulte":
        return schema.PENTE_CHOICES
    if field_name == "cheminement_ext_pente_longueur":
        return schema.PENTE_LENGTH_CHOICES
    if field_name == "labels":
        return schema.LABEL_CHOICES
    if field_name == "labels_familles_handicap":
        return schema.HANDICAP_CHOICES
    if field_name == "entree_porte_manoeuvre":
        return schema.PORTE_MANOEUVRE_CHOICES
    if field_name == "entree_porte_type":
        return schema.PORTE_TYPE_CHOICES

    return None


def generate_example_text(field_name, field):
    text = ""
    enum = get_linked_enum(field_name)
    if field.get("type") == "boolean":
        text = "True"
    elif field.get("type") == "number":
        text = "0"
    elif field.get("type") == "string" and not enum:
        pass
    elif enum:
        values = [f"{e[0]} -> {e[1]}" for e in enum if e[0] is not None]
        text = f"Valeurs possibles: {', '.join(values)}"

    return text
