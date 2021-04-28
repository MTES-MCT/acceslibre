from dataclasses import asdict

from erp.export.models import EtalabModel
from erp.schema import FIELDS
from frictionless import Schema, Field


def map_types(from_format):
    if from_format == "number":
        return "integer"
    return from_format


table_schema = Schema("base-schema.json")
fields_name = asdict(EtalabModel(id="")).keys()

for field_name in fields_name:
    f = FIELDS.get(field_name)
    if not f:
        continue

    table_schema.add_field(
        Field(
            name=field_name,
            type=map_types(f.get("type")),
        )
    )
table_schema.to_json("test.json")
