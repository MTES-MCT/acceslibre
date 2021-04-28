from dataclasses import dataclass, fields
from typing import Literal, Set, Optional


@dataclass
class EtalabModel:
    id: str
    transport_station_presence: bool = None
    transport_information: str = None
    stationnement_presence: bool = None
    stationnement_pmr: bool = None
    stationnement_ext_presence: bool = None
    stationnement_ext_pmr: bool = None
    cheminement_ext_presence: bool = None
    cheminement_ext_terrain_accidente: bool = None
    cheminement_ext_plain_pied: bool = None
    cheminement_ext_ascenseur: bool = None
    cheminement_ext_nombre_marches: int = None
    cheminement_ext_reperage_marches: bool = None
    cheminement_ext_main_courante: bool = None
    cheminement_ext_rampe: Literal["aucune", "fixe", "amovible"] = None
    cheminement_ext_pente: Literal["aucune", "légère", "importante"] = None
    cheminement_ext_devers: Literal["aucun", "léger", "important"] = None
    cheminement_ext_bande_guidage: bool = None
    cheminement_ext_retrecissement: bool = None
    entree_reperage: bool = None
    entree_vitree: bool = None
    entree_vitree_vitrophanie: bool = None
    entree_plain_pied: bool = None
    entree_ascenseur: bool = None
    entree_marches: int = None
    entree_marches_reperage: bool = None
    entree_marches_main_courante: bool = None
    entree_marches_rampe: Literal["aucune", "fixe", "amovible"] = None
    entree_dispositif_appel: bool = None
    entree_dispositif_appel_type: Set[
        Literal["bouton", "sonnette", "interphone", "visiophone"]
    ] = None
    entree_balise_sonore: bool = None
    entree_aide_humaine: bool = None
    entree_largeur_mini: int = None
    entree_pmr: bool = None
    entree_pmr_informations: str = None
    accueil_visibilite: bool = None
    accueil_personnels: Literal["formés", "non-formés"] = None
    accueil_equipements_malentendants_presence: bool = None
    accueil_equipements_malentendants: Set[
        Literal["autres", "bim", "lsf", "scd", "lpc"]
    ] = None
    accueil_cheminement_plain_pied: bool = None
    accueil_cheminement_ascenseur: bool = None
    accueil_cheminement_nombre_marches: int = None
    accueil_cheminement_reperage_marches: bool = None
    accueil_cheminement_main_courante: bool = None
    accueil_cheminement_rampe: Literal[
        "aucune", "fixe", "amovible", "aide humaine"
    ] = None
    accueil_retrecissement: bool = None
    accueil_prestations: str = None
    sanitaires_presence: bool = None
    sanitaires_adaptes: int = None
    labels: Set[Literal["autre", "dpt", "mobalib", "th"]] = None
    labels_familles_handicap: Set[
        Literal["auditif", "mental", "moteur", "visuel"]
    ] = None
    labels_autre: str = None
    commentaire: str = None
    registre_url: str = None
    conformite: bool = None


ETALAB_SCHEMA_FIELDS = [x.name for x in fields(EtalabModel)]
