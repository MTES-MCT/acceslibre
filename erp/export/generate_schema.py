import json
from typing import Any

from frictionless import Field, Schema
from frictionless.fields import ArrayField, BooleanField

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
    table_schema = Schema.from_descriptor(base)

    descriptor = table_schema.to_descriptor()
    descriptor["path"] = repository + "schema.json"
    descriptor["resources"][0]["path"] = repository + "exemple-valide.csv"

    field_types = []
    for field_name in EtalabMapper.headers():
        f = FIELDS.get(field_name)
        if not f:
            continue

        # cast to str to avoid working with proxy (due to lazy translations)
        for attr in ("label", "description", "help_text", "help_text_ui", "help_text_ui_neg"):
            if f.get(attr):
                f[attr] = str(f[attr])

        field_types, field = create_field(field_types, field_name, f)
        descriptor["fields"].append(field.to_descriptor())

    new_schema = Schema.from_descriptor(descriptor)
    for field_name, field_type in field_types:
        new_schema.set_field_type(field_name, field_type)

    new_schema.to_json(outfile)


def create_field(field_types, field_name, field):
    constraints = get_constraints(field_name, field)
    field_type = map_types(field.get("type"))

    if field_type == "boolean":
        schema_field = BooleanField(
            name=field_name,
            description=get_description(field_name, field),
            title=field.get("label"),
            constraints=constraints.get("simple", None),
            format=constraints.get("format", None),
            true_values=constraints.get("boolTrue", None),
            false_values=constraints.get("boolFalse", None),
        )
    elif constraints.get("arrayItem"):
        schema_field = ArrayField(
            name=field_name,
            description=get_description(field_name, field),
            title=field.get("label"),
            constraints=constraints.get("simple", None),
            format=constraints.get("format", None),
            array_item=constraints.get("arrayItem", None),
        )
    else:
        schema_field = Field(
            name=field_name,
            description=get_description(field_name, field),
            title=field.get("label"),
            constraints=constraints.get("simple", None),
            format=constraints.get("format", None),
        )

    field_types.append(
        (field_name, field_type),
    )

    schema_field.example = field.get("example", generate_example_text(field))

    return field_types, schema_field


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
        return json.dumps([value for value, _ in enum if value is not None])
    return ""
