from dataclasses import fields
from typing import List, Tuple

from django.contrib.gis.geos import Point

from erp import schema
from erp.export.models import ETALAB_SCHEMA_FIELDS, EtalabModel
from erp.models import Erp, Accessibilite


def map_value_from_schema(schema_enum, data):
    return schema_enum[[y[0] for y in schema_enum].index(data)][0]


def map_list_from_schema(schema_enum, data):
    if not data or not len(data):
        return None

    result = set()
    for d in data:
        choice = schema_enum[[y[0] for y in schema_enum].index(d)][0]
        result.add(choice)

    return list(result)


def map_erp_to_json_schema(erps: List[Erp]) -> Tuple[List[str], List[EtalabModel]]:
    headers = ETALAB_SCHEMA_FIELDS

    results = []
    for erp in erps:
        try:
            erp.accessibilite
        except Accessibilite.DoesNotExist:
            continue

        o = EtalabModel(
            id=str(erp.id),
            name=erp.nom,
            postal_code=erp.code_postal,
            commune=erp.commune,
            siret=erp.siret,
            numero=erp.numero,
            voie=erp.voie,
            lieu_dit=erp.lieu_dit,
            code_insee=erp.code_insee,
            coordinates=",".join(map(str, erp.geom.coords)),
            transport_station_presence=erp.accessibilite.transport_station_presence,
            stationnement_presence=erp.accessibilite.stationnement_presence,
            stationnement_pmr=erp.accessibilite.stationnement_pmr,
            stationnement_ext_presence=erp.accessibilite.stationnement_ext_presence,
            stationnement_ext_pmr=erp.accessibilite.stationnement_ext_pmr,
            cheminement_ext_presence=erp.accessibilite.cheminement_ext_presence,
            cheminement_ext_terrain_accidente=erp.accessibilite.cheminement_ext_terrain_accidente,
            cheminement_ext_plain_pied=erp.accessibilite.cheminement_ext_plain_pied,
            cheminement_ext_ascenseur=erp.accessibilite.cheminement_ext_ascenseur,
            cheminement_ext_nombre_marches=erp.accessibilite.cheminement_ext_nombre_marches,
            cheminement_ext_reperage_marches=erp.accessibilite.cheminement_ext_reperage_marches,
            cheminement_ext_main_courante=erp.accessibilite.cheminement_ext_main_courante,
            cheminement_ext_rampe=map_value_from_schema(
                schema.RAMPE_CHOICES, erp.accessibilite.cheminement_ext_rampe
            ),
            cheminement_ext_pente_presence=erp.accessibilite.cheminement_ext_pente_presence,
            cheminement_ext_pente_longueur=map_value_from_schema(
                schema.PENTE_LENGTH_CHOICES,
                erp.accessibilite.cheminement_ext_pente_longueur,
            ),
            cheminement_ext_pente_degre_difficulte=map_value_from_schema(
                schema.PENTE_CHOICES,
                erp.accessibilite.cheminement_ext_pente_degre_difficulte,
            ),
            cheminement_ext_devers=map_value_from_schema(
                schema.DEVERS_CHOICES, erp.accessibilite.cheminement_ext_devers
            ),
            cheminement_ext_bande_guidage=erp.accessibilite.cheminement_ext_bande_guidage,
            cheminement_ext_retrecissement=erp.accessibilite.cheminement_ext_retrecissement,
            entree_reperage=erp.accessibilite.entree_reperage,
            entree_vitree=erp.accessibilite.entree_vitree,
            entree_vitree_vitrophanie=erp.accessibilite.entree_vitree_vitrophanie,
            entree_plain_pied=erp.accessibilite.entree_plain_pied,
            entree_ascenseur=erp.accessibilite.entree_ascenseur,
            entree_marches=erp.accessibilite.entree_marches,
            entree_marches_reperage=erp.accessibilite.entree_marches_reperage,
            entree_marches_main_courante=erp.accessibilite.entree_marches_main_courante,
            entree_marches_rampe=map_value_from_schema(
                schema.RAMPE_CHOICES, erp.accessibilite.entree_marches_rampe
            ),
            entree_dispositif_appel=erp.accessibilite.entree_dispositif_appel,
            entree_dispositif_appel_type=map_list_from_schema(
                schema.DISPOSITIFS_APPEL_CHOICES,
                erp.accessibilite.entree_dispositif_appel_type,
            ),
            entree_balise_sonore=erp.accessibilite.entree_balise_sonore,
            entree_aide_humaine=erp.accessibilite.entree_aide_humaine,
            entree_largeur_mini=erp.accessibilite.entree_largeur_mini,
            entree_pmr=erp.accessibilite.entree_pmr,
            accueil_visibilite=erp.accessibilite.accueil_visibilite,
            accueil_personnels=map_value_from_schema(
                schema.PERSONNELS_CHOICES, erp.accessibilite.accueil_personnels
            ),
            accueil_equipements_malentendants_presence=erp.accessibilite.accueil_equipements_malentendants_presence,
            accueil_equipements_malentendants=map_list_from_schema(
                schema.EQUIPEMENT_MALENTENDANT_CHOICES,
                erp.accessibilite.accueil_equipements_malentendants,
            ),
            accueil_cheminement_plain_pied=erp.accessibilite.accueil_cheminement_plain_pied,
            accueil_cheminement_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            accueil_cheminement_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            accueil_cheminement_reperage_marches=erp.accessibilite.accueil_cheminement_reperage_marches,
            accueil_cheminement_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            accueil_cheminement_rampe=map_value_from_schema(
                schema.RAMPE_CHOICES, erp.accessibilite.accueil_cheminement_rampe
            ),
            accueil_retrecissement=erp.accessibilite.accueil_retrecissement,
            sanitaires_presence=erp.accessibilite.sanitaires_presence,
            sanitaires_adaptes=erp.accessibilite.sanitaires_adaptes,
            labels=map_list_from_schema(schema.LABEL_CHOICES, erp.accessibilite.labels),
            labels_familles_handicap=map_list_from_schema(
                schema.HANDICAP_CHOICES, erp.accessibilite.labels_familles_handicap
            ),
            registre_url=erp.accessibilite.registre_url,
            conformite=erp.accessibilite.conformite,
            cheminement_ext_sens_marches=map_value_from_schema(
                schema.ESCALIER_SENS, erp.accessibilite.cheminement_ext_sens_marches
            ),
            entree_marches_sens=map_value_from_schema(
                schema.ESCALIER_SENS, erp.accessibilite.entree_marches_sens
            ),
            accueil_cheminement_sens_marches=map_value_from_schema(
                schema.ESCALIER_SENS, erp.accessibilite.accueil_cheminement_sens_marches
            ),
            entree_porte_presence=erp.accessibilite.entree_porte_presence,
            entree_porte_manoeuvre=map_value_from_schema(
                schema.PORTE_MANOEUVRE_CHOICES, erp.accessibilite.entree_porte_manoeuvre
            ),
            entree_porte_type=map_value_from_schema(
                schema.PORTE_TYPE_CHOICES, erp.accessibilite.entree_porte_type
            ),
        )

        results.append(o)

    return headers, results
