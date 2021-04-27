from erp import schema
from frictionless import Schema, Field

table_schema = Schema("base-schema.json")
table_schema.add_field(
    Field(
        name="",
        type="",
    )
)
table_schema.to_json("test.json")
