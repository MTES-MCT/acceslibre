from dataclasses import dataclass
from typing import Literal, Set


@dataclass
class OfficialSchema:
    id: str
    transport_station_presence: bool
    transport_information: str
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
    cheminement_ext_main_courante: bool
    cheminement_ext_rampe: Literal["aucune", "fixe", "amovible"]
    cheminement_ext_pente: Literal["aucune", "légère", "importante"]
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
    entree_dispositif_appel: bool
    entree_dispositif_appel_type: Set[
        Literal["bouton", "sonnette", "interphone", "visiophone"]
    ]
    entree_balise_sonore: bool
    entree_aide_humaine: bool
    entree_largeur_mini: int
    entree_pmr: bool
    entree_pmr_informations: str
    accueil_visibilite: bool
    accueil_personnels: Literal["formés", "non-formés"]
    accueil_equipements_malentendants_presence: bool
    accueil_equipements_malentendants: Set[
        Literal["autres", "bim", "lsf", "scd", "lpc"]
    ]
    accueil_cheminement_plain_pied: bool
    accueil_cheminement_ascenseur: bool
    accueil_cheminement_nombre_marches: int
    accueil_cheminement_reperage_marches: bool
    accueil_cheminement_main_courante: bool
    accueil_cheminement_rampe: Literal["aucune", "fixe", "amovible", "aide humaine"]
    accueil_retrecissement: bool
    accueil_prestations: str
    sanitaires_presence: bool
    sanitaires_adaptes: int
    labels: Set[Literal["autre", "dpt", "mobalib", "th"]]
    labels_familles_handicap: Set[Literal["auditif", "mental", "moteur", "visuel"]]
    labels_autre: str
    commentaire: str
    registre_url: str
    conformite: bool
