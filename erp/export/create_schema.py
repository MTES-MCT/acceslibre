from frictionless import Schema

table_schema = Schema("base-schema.json")
table_schema.to_json("test.json")
