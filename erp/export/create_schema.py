from dataclasses import asdict

from frictionless import Schema, Field

from erp import schema
from erp.export.models import EtalabModel
from erp.schema import FIELDS


ETALAB_SCHEMA_FIELDS = [
    "id",
    "transport_station_presence",
    "transport_information",
    "stationnement_presence",
    "stationnement_pmr",
    "stationnement_ext_presence",
    "stationnement_ext_pmr",
    "cheminement_ext_presence",
    "cheminement_ext_terrain_accidente",
    "cheminement_ext_plain_pied",
    "cheminement_ext_ascenseur",
    "cheminement_ext_nombre_marches",
    "cheminement_ext_reperage_marches",
    "cheminement_ext_main_courante",
    "cheminement_ext_rampe",
    "cheminement_ext_pente",
    "cheminement_ext_devers",
    "cheminement_ext_bande_guidage",
    "cheminement_ext_retrecissement",
    "entree_reperage",
    "entree_vitree",
    "entree_vitree_vitrophanie",
    "entree_plain_pied",
    "entree_ascenseur",
    "entree_marches",
    "entree_marches_reperage",
    "entree_marches_main_courante",
    "entree_marches_rampe",
    "entree_dispositif_appel",
    "entree_dispositif_appel_type",
    "entree_balise_sonore",
    "entree_aide_humaine",
    "entree_largeur_mini",
    "entree_pmr",
    "entree_pmr_informations",
    "accueil_visibilite",
    "accueil_personnels",
    "accueil_equipements_malentendants_presence",
    "accueil_equipements_malentendants",
    "accueil_cheminement_plain_pied",
    "accueil_cheminement_ascenseur",
    "accueil_cheminement_nombre_marches",
    "accueil_cheminement_reperage_marches",
    "accueil_cheminement_main_courante",
    "accueil_cheminement_rampe",
    "accueil_retrecissement",
    "accueil_prestations",
    "sanitaires_presence",
    "sanitaires_adaptes",
    "labels",
    "labels_autre",
    "commentaire",
    "registre_url",
    "conformite",
]


def generate_schema(base="base-schema.json", outfile="schema.json"):
    table_schema = Schema(base)
    # table_schema["version"] = "0.0.1"

    for field_name in ETALAB_SCHEMA_FIELDS:
        f = FIELDS.get(field_name)
        if not f:
            continue

        table_schema.add_field(create_field(field_name, f))

    table_schema.to_json(outfile)


def create_field(field_name, field):
    constraints = get_constraints(field_name, field)
    return Field(
        name=field_name,
        type=map_types(field.get("type")),
        description=field.get("help_text_ui") or field.get("description"),
        title=field.get("label"),
        constraints=constraints.get("enum", None),
        array_item=constraints.get("arrayItem", None),
    )


def map_types(from_format):
    if from_format == "number":
        return "integer"
    return from_format


def get_constraints(field_name, field):
    """
    Get TableSchema constraints. The key will be identified when constructing fields to avoid another conditional
    :param field:
    :param name:
    :return:
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

    return constraints


def get_linked_enum(field_name):
    if field_name == "cheminement_ext_devers":
        return schema.DEVERS_CHOICES
    if field_name == "entree_marches_rampe":
        return schema.RAMPE_CHOICES
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
    if field_name == "cheminement_ext_pente_degre_difficulte":
        return schema.PENTE_CHOICES
    if field_name == "cheminement_ext_pente_longueur":
        return schema.PENTE_LENGTH_CHOICES
    if field_name == "labels":
        return schema.LABEL_CHOICES
    if field_name == "labels_familles_handicap":
        return schema.HANDICAP_CHOICES

    return None


generate_schema()
