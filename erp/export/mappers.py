from dataclasses import fields
from typing import List, Tuple, Literal

from erp import schema
from erp.export.schemas import OfficialSchema
from erp.models import Erp, Accessibilite


def map_erp_to_official_schema(erps: List[Erp]) -> Tuple[List[str], List[OfficialSchema]]:
    headers = [x.name for x in fields(OfficialSchema)]

    def map_accueil_personnels(data):
        return schema.PERSONNELS_CHOICES[data] or None

    def map_accueil_equipements_malentendants(data):
        if not len(data):
            return None

        result = set()
        for d in data:
            result.add(schema.EQUIPEMENT_MALENTENDANT_CHOICES[d])

        return result

    def map_rampe(data) -> Literal["Absence", "Fixe", "Amovible"]:
        return schema.RAMPE_CHOICES[data] or None

    def map_cheminement_pente(data):
        return schema.PENTE_CHOICES[data] or None

    def map_cheminement_devers(data):
        return schema.DEVERS_CHOICES[data] or None

    def map_dispositif_appel(data):
        return schema.DISPOSITIFS_APPEL_CHOICES[data] or None

    results = []
    for erp in erps:
        try:
            erp.accessibilite
        except Accessibilite.DoesNotExist:
            continue

        o = OfficialSchema(
            id=str(erp.id),
            transport_station_presence=erp.accessibilite.transport_station_presence,
            transport_information=erp.accessibilite.transport_information,
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
            cheminement_ext_rampe=map_rampe(erp.accessibilite.cheminement_ext_rampe),
            cheminement_ext_pente=map_cheminement_pente(erp.accessibilite.cheminement_ext_pente),
            cheminement_ext_devers=map_cheminement_devers(erp.accessibilite.cheminement_ext_devers),
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
            entree_marches_rampe=map_rampe(erp.accessibilite.entree_marches_rampe),
            entree_dispositif_appel=erp.accessibilite.entree_dispositif_appel,
            entree_dispositif_appel_type=map_dispositif_appel(erp.accessibilite.entree_dispositif_appel_type),
            entree_balise_sonore=erp.accessibilite.entree_balise_sonore,
            entree_aide_humaine=erp.accessibilite.entree_aide_humaine,
            entree_largeur_mini=erp.accessibilite.entree_largeur_mini,
            entree_pmr=erp.accessibilite.entree_pmr,
            entree_pmr_informations=erp.accessibilite.entree_pmr_informations,
            accueil_visibilite=erp.accessibilite.accueil_visibilite,
            accueil_personnels=map_accueil_personnels(erp.accessibilite.accueil_personnels),
            accueil_equipements_malentendants_presence=erp.accessibilite.accueil_equipements_malentendants_presence,
            accueil_equipements_malentendants=map_accueil_equipements_malentendants(erp.accessibilite.accueil_equipements_malentendants),
            accueil_cheminement_plain_pied=erp.accessibilite.accueil_cheminement_plain_pied,
            accueil_cheminement_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            accueil_cheminement_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            accueil_cheminement_reperage_marches=erp.accessibilite.accueil_cheminement_reperage_marches,
            accueil_cheminement_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            accueil_cheminement_rampe=map_rampe(erp.accessibilite.accueil_cheminement_rampe),
            accueil_retrecissement=erp.accessibilite.accueil_retrecissement,
            accueil_prestations=erp.accessibilite.accueil_prestations,
            sanitaires_presence=erp.accessibilite.sanitaires_presence,
            sanitaires_adaptes=erp.accessibilite.sanitaires_adaptes,
            labels=erp.accessibilite.labels,
            labels_familles_handicap=erp.accessibilite.labels_familles_handicap,
            labels_autre=erp.accessibilite.labels_autre,
            commentaire=erp.accessibilite.commentaire,
            registre_url=erp.accessibilite.registre_url,
            conformite=erp.accessibilite.conformite
        )

        results.append(o)

    return headers, results
