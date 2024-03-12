from typing import Any

from frictionless import Field, Schema

from erp.export.mappers import EtalabMapper
from erp.schema import FIELDS, get_bdd_values

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

    for field_name in EtalabMapper.headers():
        f = FIELDS.get(field_name)
        if not f:
            continue

        # cast to str to avoid working with proxy (due to lazy translations)
        for attr in ("label", "description", "help_text", "help_text_ui", "help_text_ui_neg"):
            if f.get(attr):
                f[attr] = str(f[attr])

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

    schema_field["example"] = field.get("example", generate_example_text(field))

    return schema_field


def get_description(field_name, field):
    help_text = field.get("help_text").replace("&nbsp;", " ") if field.get("help_text") else None
    description = field.get("description") or field.get("help_text_ui") or help_text
    if not description:
        raise ValueError("No description found for field: " + field_name)
    if field.get("choices") and field.get("type") in ("string", "array"):
        values = [f"{e[0]} -> {e[1]}" for e in field.get("choices") if e[0] is not None]
        description += f". Valeurs possibles: {', '.join(values)}"

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
    enum = field.get("choices") or None
    bdd_values = field.get("app_model") or None

    field_type = map_types(field.get("type"))
    if enum and field_type == "string":
        constraints["simple"] = {}

        constraints["simple"]["enum"] = [value[0] for value in enum if value[0] is not None]
    elif enum and field_type == "array":
        constraints["arrayItem"] = {}
        constraints["arrayItem"]["type"] = "string"
        constraints["arrayItem"]["enum"] = [value[0] for value in enum if value[0] is not None]
    elif bdd_values:
        constraints["arrayItem"] = {}
        constraints["arrayItem"]["type"] = "string"
        constraints["arrayItem"]["enum"] = [*get_bdd_values(field_name)]
    elif field_type == "boolean":
        constraints["boolTrue"] = TRUE_VALUES
        constraints["boolFalse"] = FALSE_VALUES
    elif field_type == "string" and "url" in field_name:
        constraints["format"] = "uri"

    return constraints


def generate_example_text(field):
    enum = field.get("choices") or None
    if field.get("type") == "boolean":
        return "True"
    if field.get("type") == "number":
        return "0"
    if field.get("type") == "string" and not enum:
        return ""
    if enum:
        return str([value for value, _ in enum])
    return ""
