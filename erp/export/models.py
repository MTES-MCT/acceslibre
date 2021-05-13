from dataclasses import dataclass, fields
from typing import Literal, Set, Optional

from erp import schema
from erp.export.utils import (
    map_value_from_schema,
    map_list_from_schema,
    map_coords,
    BaseExportModel,
)


@dataclass
class EtalabModel(BaseExportModel):
    id: str
    name: str
    postal_code: str
    commune: str
    numero: str
    voie: str
    lieu_dit: str
    code_insee: str
    siret: str
    coordinates: str
    transport_station_presence: bool
    stationnement_presence: bool
    stationnement_pmr: bool
    stationnement_ext_presence: bool
    stationnement_ext_pmr: bool
    cheminement_ext_presence: bool
    cheminement_ext_terrain_accidente: bool
    cheminement_ext_plain_pied: bool
    cheminement_ext_ascenseur: bool
    cheminement_ext_nombre_marches: int
    cheminement_ext_reperage_marches: bool
    cheminement_ext_sens_marches: Literal["montant", "descendant"]
    cheminement_ext_main_courante: bool
    cheminement_ext_rampe: Literal["aucune", "fixe", "amovible"]
    cheminement_ext_pente_presence: bool
    cheminement_ext_pente_degre_difficulte: Literal["aucune", "légère", "importante"]
    cheminement_ext_pente_longueur: Literal["courte", "moyenne", "longue"]
    cheminement_ext_devers: Literal["aucun", "léger", "important"]
    cheminement_ext_bande_guidage: bool
    cheminement_ext_retrecissement: bool
    entree_reperage: bool
    entree_vitree: bool
    entree_vitree_vitrophanie: bool
    entree_plain_pied: bool
    entree_ascenseur: bool
    entree_marches: int
    entree_marches_reperage: bool
    entree_marches_main_courante: bool
    entree_marches_rampe: Literal["aucune", "fixe", "amovible"]
    entree_marches_sens: Literal["montant", "descendant"]
    entree_dispositif_appel: bool
    entree_dispositif_appel_type: Optional[
        Set[Literal["bouton", "interphone", "visiophone"]]
    ]
    entree_balise_sonore: bool
    entree_aide_humaine: bool
    entree_largeur_mini: int
    entree_pmr: bool
    entree_porte_presence: bool
    entree_porte_manoeuvre: Literal["battante", "coulissante", "tourniquet", "tambour"]
    entree_porte_type: Literal["manuelle", "automatique"]
    accueil_visibilite: bool
    accueil_personnels: Literal["formés", "non-formés"]
    accueil_equipements_malentendants_presence: bool
    accueil_equipements_malentendants: Optional[
        Set[Literal["autres", "bim", "lsf", "scd", "lpc"]]
    ]
    accueil_cheminement_plain_pied: bool
    accueil_cheminement_ascenseur: bool
    accueil_cheminement_nombre_marches: int
    accueil_cheminement_reperage_marches: bool
    accueil_cheminement_main_courante: bool
    accueil_cheminement_rampe: Literal["aucune", "fixe", "amovible", "aide humaine"]
    accueil_cheminement_sens_marches: Literal["montant", "descendant"]
    accueil_retrecissement: bool
    sanitaires_presence: bool
    sanitaires_adaptes: int
    labels: Optional[Set[Literal["autre", "dpt", "mobalib", "th"]]]
    labels_familles_handicap: Optional[
        Set[Literal["auditif", "mental", "moteur", "visuel"]]
    ]
    registre_url: str
    conformite: bool

    @staticmethod
    def headers():
        return [x.name for x in fields(EtalabModel)]

    @staticmethod
    def map_from(erp):
        return EtalabModel(
            id=str(erp.id),
            name=erp.nom,
            postal_code=erp.code_postal,
            commune=erp.commune,
            numero=erp.numero,
            voie=erp.voie,
            lieu_dit=erp.lieu_dit,
            code_insee=erp.code_insee,
            siret=erp.siret,
            coordinates=map_coords(erp.geom),
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
