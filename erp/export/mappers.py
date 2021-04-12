from dataclasses import fields
from typing import List, Tuple

from erp.export.schemas import OfficialSchema, OfficialSchemaV2
from erp.models import Erp
from erp import schema


def map_erp_to_official_schema(erps: List[Erp]) -> Tuple[List[str], List[OfficialSchema]]:
    headers = [x.name for x in fields(OfficialSchema)]

    results = []
    for erp in erps:
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
            cheminement_ext_rampe=erp.accessibilite.cheminement_ext_rampe,
            cheminement_ext_pente=erp.accessibilite.cheminement_ext_pente,
            cheminement_ext_devers=erp.accessibilite.cheminement_ext_devers,
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
            entree_marches_rampe=erp.accessibilite.entree_marches_rampe,
            entree_dispositif_appel=erp.accessibilite.entree_dispositif_appel,
            entree_dispositif_appel_type=erp.accessibilite.entree_dispositif_appel_type,
            entree_balise_sonore=erp.accessibilite.entree_balise_sonore,
            entree_aide_humaine=erp.accessibilite.entree_aide_humaine,
            entree_largeur_mini=erp.accessibilite.entree_largeur_mini,
            entree_pmr=erp.accessibilite.entree_pmr,
            entree_pmr_informations=erp.accessibilite.entree_pmr_informations,
            accueil_visibilite=erp.accessibilite.accueil_visibilite,
            accueil_personnels=erp.accessibilite.accueil_personnels,
            accueil_equipements_malentendants_presence=erp.accessibilite.accueil_equipements_malentendants_presence,
            accueil_equipements_malentendants=erp.accessibilite.accueil_equipements_malentendants,
            accueil_cheminement_plain_pied=erp.accessibilite.accueil_cheminement_plain_pied,
            accueil_cheminement_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            accueil_cheminement_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            accueil_cheminement_reperage_marches=erp.accessibilite.accueil_cheminement_reperage_marches,
            accueil_cheminement_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            accueil_cheminement_rampe=erp.accessibilite.accueil_cheminement_rampe,
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


def map_erp_to_official_schema_v2(erps: List[Erp]) -> Tuple[List[str], List[OfficialSchemaV2]]:
    headers = [x.name for x in fields(OfficialSchemaV2)]

    def map_accueil_personnels(data):
        if data == schema.PERSONNELS_AUCUN:
            return "Absence de personnel"
        elif data == schema.PERSONNELS_NON_FORMES:
            return "Personnel non-formé"
        elif data == schema.PERSONNELS_FORMES:
            return "Personnel formé"

        return None

    def map_accueil_equipements_malentendants(data):
        if not len(data):
            return None

        result = set()
        for d in data:
            if data == schema.EQUIPEMENT_MALENTENDANT_LPC:
                results.add("LSF")
            elif data == schema.EQUIPEMENT_MALENTENDANT_SCD:
                results.add("ST")
            elif data == schema.EQUIPEMENT_MALENTENDANT_BIM:
                results.add("BIM")
            elif data == schema.EQUIPEMENT_MALENTENDANT_LSF:
                results.add("LSF")
            elif data == schema.EQUIPEMENT_MALENTENDANT_AUTRES:
                continue

        return result

    def map_rampe(data):
        if data == schema.RAMPE_FIXE:
            return "Fixe"
        elif data == schema.RAMPE_AMOVIBLE:
            return "Amovible"
        elif data == schema.RAMPE_AIDE_HUMAINE:
            return "Fixe"
        elif data == schema.RAMPE_AUCUNE:
            return "Absence"

        return None

    def map_cheminement_pente(data):
        if data == schema.PENTE_AUCUNE:
            return "Aucune"
        elif data == schema.PENTE_LEGERE:
            return "Courte"
        elif data == schema.PENTE_IMPORTANTE:
            return "Longue"

        return None

    # TODO: well ...
    def map_cheminement_devers(data):
        if data == schema.DEVERS_AUCUN:
            return 0
        elif data == schema.DEVERS_LEGER:
            return 1
        elif data == schema.DEVERS_IMPORTANT:
            return 2

        return None

    def map_cheminement_revetement(data):
        if data:
            return "Constamment meuble"
        elif not data:
            return "Non meuble"

        return None

    # TODO how to ?
    def map_systeme_guidage(data):
        if not len(data):
            return None

        result = set()
        return result

    def map_controle_acces(data):
        if data == schema.DISPOSITIFS_APPEL_BOUTON:
            return "Bouton d'appel"
        elif data == schema.DISPOSITIFS_APPEL_SONNETTE:
            return "Bouton d'appel"
        elif data == schema.DISPOSITIFS_APPEL_INTERPHONE:
            return "Interphone"
        elif data == schema.DISPOSITIFS_APPEL_VISIOPHONE:
            return "Visiophone"

        return None

    results = []
    for erp in erps:
        o = OfficialSchemaV2(
            id=str(erp.id),
            accueil_personnels=map_accueil_personnels(erp.accessibilite.accueil_personnels),
            accueil_aide_audition=erp.accessibilite.accueil_equipements_malentendants_presence,
            accueil_equipements_malentendants = map_accueil_equipements_malentendants(erp.accessibilite.accueil_equipements_malentendants),
            accueil_prestations=erp.accessibilite.accueil_prestations,
            sanitaires_erp=erp.accessibilite.sanitaires_presence,
            sanitaires_adaptes=erp.accessibilite.sanitaires_adaptes,
            stationnement_erp=erp.accessibilite.stationnement_ext_presence or erp.accessibilite.stationnement_presence,
            stationnement_pmr=erp.accessibilite.stationnement_ext_pmr or erp.accessibilite.stationnement_pmr,
            cheminement_plain_pied=erp.accessibilite.cheminement_ext_plain_pied,
            cheminement_rampe=map_rampe(erp.accessibilite.cheminement_ext_rampe),
            cheminement_rampe_sonnette=erp.accessibilite.entree_balise_sonore,
            cheminement_ascenseur=erp.accessibilite.cheminement_ext_ascenseur,
            cheminement_escalier_nombre_marches=erp.accessibilite.cheminement_ext_nombre_marches,
            cheminement_escalier_main_courante=erp.accessibilite.cheminement_ext_main_courante,
            cheminement_exterieur=True,
            cheminement_pente=map_cheminement_pente(erp.accessibilite.cheminement_ext_pente),
            cheminement_devers=map_cheminement_devers(erp.accessibilite.cheminement_ext_devers),
            cheminement_revetement=map_cheminement_revetement(erp.accessibilite.cheminement_ext_terrain_accidente),
            cheminement_reperage_elts_vitre=erp.accessibilite.entree_vitree_vitrophanie,
            cheminement_systeme_guidage=map_systeme_guidage([]),
            cheminement_largeur_mini=erp.accessibilite.entree_largeur_mini,
            cheminement_1_plain_pied=erp.accessibilite.accueil_cheminement_plain_pied,
            cheminement_1_rampe=map_rampe(erp.accessibilite.accueil_cheminement_rampe),
            cheminement_1_rampe_sonnette=erp.accessibilite.entree_balise_sonore,
            cheminement_1_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            cheminement_1_escalier_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            cheminement_1_escalier_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            cheminement_1_exterieur=False,
            cheminement_1_pente=map_cheminement_pente(erp.accessibilite.cheminement_ext_pente),
            cheminement_1_devers=map_cheminement_devers(erp.accessibilite.cheminement_ext_devers),
            cheminement_1_revetement=map_cheminement_revetement(erp.accessibilite.cheminement_ext_terrain_accidente),
            cheminement_1_reperage_elts_vitre=erp.accessibilite.entree_vitree_vitrophanie,
            cheminement_1_systeme_guidage=map_systeme_guidage([]),
            cheminement_1_largeur_mini=erp.accessibilite.entree_largeur_mini,
            entree_type="Site",
            entree_plain_pied=erp.accessibilite.entree_plain_pied,
            entree_rampe=map_rampe(erp.accessibilite.entree_marches_rampe),
            entree_rampe_sonnette=erp.accessibilite.entree_balise_sonore,
            entree_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            entree_escalier_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            entree_escalier_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            entree_reperabilite=erp.accessibilite.entree_reperage,
            entree_reperage_elts_vitre=erp.accessibilite.entree_vitree_vitrophanie,
            entree_signaletique=erp.accessibilite.entree_reperage,
            entree_controle_acces=map_controle_acces(erp.accessibilite.entree_dispositif_appel_type),
            entree_type_porte=None,  # TODO
            entree_accueil_visible=erp.accessibilite.accueil_visibilite,
            entree_1_type="Site",
            entree_1_plain_pied=erp.accessibilite.entree_plain_pied,
            entree_1_rampe=map_rampe(erp.accessibilite.entree_marches_rampe),
            entree_1_rampe_sonnette=erp.accessibilite.entree_balise_sonore,
            entree_1_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            entree_1_escalier_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            entree_1_escalier_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            entree_1_reperabilite=erp.accessibilite.entree_reperage,
            entree_1_reperage_elts_vitre=erp.accessibilite.entree_vitree_vitrophanie,
            entree_1_signaletique=erp.accessibilite.entree_reperage,
            entree_1_controle_acces=map_controle_acces(erp.accessibilite.entree_dispositif_appel_type),
            entree_1_type_porte=None, # TODO
            entree_1_accueil_visible=erp.accessibilite.accueil_visibilite,
            # transport_station_presence=erp.accessibilite.transport_station_presence,
            # transport_information=erp.accessibilite.transport_information,
            # stationnement_presence=erp.accessibilite.stationnement_presence,
            # stationnement_pmr=erp.accessibilite.stationnement_pmr,
            # stationnement_ext_presence=erp.accessibilite.stationnement_ext_presence,
            # stationnement_ext_pmr=erp.accessibilite.stationnement_ext_pmr,
            # cheminement_ext_presence=erp.accessibilite.cheminement_ext_presence,
            # cheminement_ext_terrain_accidente=erp.accessibilite.cheminement_ext_terrain_accidente,
            # cheminement_ext_plain_pied=erp.accessibilite.cheminement_ext_plain_pied,
            # cheminement_ext_ascenseur=erp.accessibilite.cheminement_ext_ascenseur,
            # cheminement_ext_nombre_marches=erp.accessibilite.cheminement_ext_nombre_marches,
            # cheminement_ext_reperage_marches=erp.accessibilite.cheminement_ext_reperage_marches,
            # cheminement_ext_main_courante=erp.accessibilite.cheminement_ext_main_courante,
            # cheminement_ext_rampe=erp.accessibilite.cheminement_ext_rampe,
            # cheminement_ext_pente=erp.accessibilite.cheminement_ext_pente,
            # cheminement_ext_devers=erp.accessibilite.cheminement_ext_devers,
            # cheminement_ext_bande_guidage=erp.accessibilite.cheminement_ext_bande_guidage,
            # cheminement_ext_retrecissement=erp.accessibilite.cheminement_ext_retrecissement,
            # entree_reperage=erp.accessibilite.entree_reperage,
            # entree_vitree=erp.accessibilite.entree_vitree,
            # entree_vitree_vitrophanie=erp.accessibilite.entree_vitree_vitrophanie,
            # entree_plain_pied=erp.accessibilite.entree_plain_pied,
            # entree_ascenseur=erp.accessibilite.entree_ascenseur,
            # entree_marches=erp.accessibilite.entree_marches,
            # entree_marches_reperage=erp.accessibilite.entree_marches_reperage,
            # entree_marches_main_courante=erp.accessibilite.entree_marches_main_courante,
            # entree_marches_rampe=erp.accessibilite.entree_marches_rampe,
            # entree_dispositif_appel=erp.accessibilite.entree_dispositif_appel,
            # entree_dispositif_appel_type=erp.accessibilite.entree_dispositif_appel_type,
            # entree_balise_sonore=erp.accessibilite.entree_balise_sonore,
            # entree_aide_humaine=erp.accessibilite.entree_aide_humaine,
            # entree_largeur_mini=erp.accessibilite.entree_largeur_mini,
            # entree_pmr=erp.accessibilite.entree_pmr,
            # entree_pmr_informations=erp.accessibilite.entree_pmr_informations,
            # accueil_visibilite=erp.accessibilite.accueil_visibilite,
            # accueil_personnels=erp.accessibilite.accueil_personnels,
            # accueil_equipements_malentendants_presence=erp.accessibilite.accueil_equipements_malentendants_presence,
            # accueil_equipements_malentendants=erp.accessibilite.accueil_equipements_malentendants,
            # accueil_cheminement_plain_pied=erp.accessibilite.accueil_cheminement_plain_pied,
            # accueil_cheminement_ascenseur=erp.accessibilite.accueil_cheminement_ascenseur,
            # accueil_cheminement_nombre_marches=erp.accessibilite.accueil_cheminement_nombre_marches,
            # accueil_cheminement_reperage_marches=erp.accessibilite.accueil_cheminement_reperage_marches,
            # accueil_cheminement_main_courante=erp.accessibilite.accueil_cheminement_main_courante,
            # accueil_cheminement_rampe=erp.accessibilite.accueil_cheminement_rampe,
            # accueil_retrecissement=erp.accessibilite.accueil_retrecissement,
            # accueil_prestations=erp.accessibilite.accueil_prestations,
            # sanitaires_presence=erp.accessibilite.sanitaires_presence,
            # sanitaires_adaptes=erp.accessibilite.sanitaires_adaptes,
            # labels=erp.accessibilite.labels,
            # labels_familles_handicap=erp.accessibilite.labels_familles_handicap,
            # labels_autre=erp.accessibilite.labels_autre,
            # commentaire=erp.accessibilite.commentaire,
            # registre_url=erp.accessibilite.registre_url,
            # conformite=erp.accessibilite.conformite
        )

        results.append(o)

    return headers, results
