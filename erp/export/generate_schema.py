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
        description=get_description(field_name, field),
        title=field.get("label"),
        true_values=constraints.get("boolTrue", None),
        false_values=constraints.get("boolFalse", None),
        constraints=constraints.get("simple", None),
        array_item=constraints.get("arrayItem", None),
        format=constraints.get("format", None),
    )

    schema_field["example"] = field.get(
        "example", generate_example_text(field)
    ) or generate_example_text(field)

    return schema_field


def get_description(field_name, field):
    help_text = (
        field.get("help_text").replace("&nbsp;", " ")
        if field.get("help_text")
        else None
    )
    description = field.get("description") or field.get("help_text_ui") or help_text
    if not description:
        raise ValueError("No description found for field: " + field_name)
    return description


def map_types(from_format):
    if from_format == "number":
        return "integer"
    return from_format


def get_constraints(field_name: str, field: Any) -> dict:
    """
    Get TableSchema constraints. The key will be identified when constructing fields to avoid another conditional
    """
    constraints = {}
    enum = field.get("enum") or None
    field_type = map_types(field.get("type"))
    if enum and field_type == "string":
        constraints["simple"] = {}

        constraints["simple"]["enum"] = [
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
    elif field_type == "string" and "url" in field_name:
        constraints["format"] = "uri"

    return constraints


def generate_example_text(field):
    text = ""
    enum = field.get("enum") or None
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
