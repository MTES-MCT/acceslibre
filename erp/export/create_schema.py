from dataclasses import asdict

from erp import schema
from erp.export.models import EtalabModel
from erp.schema import FIELDS
from frictionless import Schema, Field


def map_types(from_format):
    if from_format == "number":
        return "integer"
    return from_format


def get_linked_enum(name):
    if name == "cheminement_ext_devers":
        return schema.DEVERS_CHOICES
    if name == "entree_marches_rampe":
        return schema.RAMPE_CHOICES
    if name == "entree_dispositif_appel_type":
        return schema.DISPOSITIFS_APPEL_CHOICES
    if name == "accueil_personnels":
        return schema.PERSONNELS_CHOICES
    if name == "accueil_equipements_malentendants":
        return schema.EQUIPEMENT_MALENTENDANT_CHOICES
    if name == "accueil_cheminement_sens_marches":
        return schema.ESCALIER_SENS
    if name == "accueil_cheminement_rampe":
        return schema.RAMPE_CHOICES
    if name == "cheminement_ext_pente_degre_difficulte":
        return schema.PENTE_CHOICES
    if name == "cheminement_ext_pente_longueur":
        return schema.PENTE_LENGTH_CHOICES

    return None


def create_field(name, field):
    constraints = get_constraints(field, name)

    return Field(
        name=name,
        type=map_types(field.get("type")),
        description=field.get("help_text_ui") or field.get("description"),
        title=field.get("label"),
        constraints=constraints,
    )


def get_constraints(field, name):
    constraints = {}
    enum = get_linked_enum(name)
    field_type = map_types(field.get("type"))
    if enum and field_type == "string":
        constraints["enum"] = [value[0] for value in enum if value[0] is not None]
    elif enum and field_type == "array":
        constraints["arrayItem"] = {}
        constraints["arrayItem"]["type"] = "string"
        constraints["arrayItem"]["enum"] = [
            value[0] for value in enum if value[0] is not None
        ]
    else:
        constraints = None
    return constraints


table_schema = Schema("base-schema.json")
fields_name = asdict(EtalabModel(id="")).keys()

for field_name in fields_name:
    f = FIELDS.get(field_name)
    if not f:
        continue

    table_schema.add_field(create_field(field_name, f))

table_schema.to_json("schema.json")
