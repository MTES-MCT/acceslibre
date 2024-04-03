from django.utils.translation import gettext as translate
from django.utils.translation import ngettext

from erp import schema
from erp.export.utils import map_list_from_schema


def get_parking_label(access):
    if access.stationnement_presence and access.stationnement_pmr:
        return translate("Stationnement adapté dans l'établissement")
    elif access.stationnement_ext_presence and access.stationnement_ext_pmr:
        return translate("Stationnement adapté à proximité")
    elif access.stationnement_ext_presence and access.stationnement_ext_pmr is False:
        return translate("Pas de stationnement adapté à proximité")

    return ""


def get_outside_path_label(access):
    if not access.cheminement_ext_presence:
        return ""

    if (
        access.cheminement_ext_plain_pied is True
        and access.stable_ground
        and access.easy_or_no_slope
        and access.little_or_no_camber
        and not access.cheminement_ext_retrecissement
    ):
        return translate("Chemin d'accès de plain pied")

    if (
        access.cheminement_ext_plain_pied is False
        and access.provide_stair_equipement
        and access.stable_ground
        and access.easy_or_no_slope
        and access.little_or_no_camber
        and not access.cheminement_ext_retrecissement
    ):
        equipement = translate("rampe") if access.has_ramp_exterior_path() else translate("ascenseur")
        return translate("Chemin rendu accessible (%s)") % (equipement)

    if (
        not access.stable_ground
        or not access.easy_or_no_slope
        or not access.little_or_no_camber
        or access.cheminement_ext_retrecissement
        or (not access.provide_stair_equipement and access.cheminement_ext_plain_pied is False)
    ):
        return translate("Difficulté sur le chemin d'accès")

    return ""


def get_entrance_label(access):
    if access.entree_plain_pied is True:
        if access.entrance_has_min_width:
            return translate("Entrée de plain pied")
        else:
            return translate("Entrée de plain pied mais étroite")

    if access.entree_plain_pied in (False, None) and access.entree_pmr is True:
        return translate("Entrée spécifique PMR")

    if access.entree_plain_pied is None:
        return ""

    if access.entree_ascenseur:
        if access.entrance_has_min_width:
            return translate("Accès à l'entrée par ascenseur")
        else:
            return translate("Entrée rendue accessible par ascenseur mais étroite")

    if access.entrance_has_ramp:
        if access.entrance_has_min_width:
            return translate("Accès à l'entrée par une rampe")
        else:
            return translate("Entrée rendue accessible par rampe mais étroite")

    label = translate("L'entrée n'est pas de plain-pied")
    if access.entree_aide_humaine is True:
        label += translate("\n Aide humaine possible")

    return label


def get_staff_label(access):
    if access.accueil_personnels == schema.PERSONNELS_AUCUN:
        return translate("Aucun personnel")
    elif access.accueil_personnels == schema.PERSONNELS_NON_FORMES:
        return translate("Personnel non formé")
    elif access.accueil_personnels == schema.PERSONNELS_FORMES:
        return translate("Personnel sensibilisé / formé")

    return ""


def get_sound_beacon_label(access):
    return translate("Balise sonore") if access.entree_balise_sonore else ""


def get_audiodescription_label(access):
    label = ""
    if access.accueil_audiodescription_presence and access.accueil_audiodescription:
        label = ", ".join(
            map_list_from_schema(
                schema.AUDIODESCRIPTION_CHOICES,
                access.accueil_audiodescription,
                verbose=True,
            )
        )
    return label


def get_deaf_equipment_label(access):
    label = ""
    if access.accueil_equipements_malentendants_presence and access.accueil_equipements_malentendants:
        label = ", ".join(
            map_list_from_schema(
                schema.EQUIPEMENT_MALENTENDANT_CHOICES,
                access.accueil_equipements_malentendants,
                verbose=True,
            )
        )
    return label


def get_wc_label(access):
    if access.sanitaires_presence and access.sanitaires_adaptes:
        return translate("Sanitaire adapté")
    elif access.sanitaires_presence and not access.sanitaires_adaptes:
        return translate("Sanitaire non adapté")
    return ""


def get_room_accessible_label(access):
    if not access.accueil_chambre_nombre_accessibles:
        return ""

    return ngettext(
        "%(count)d chambre accessible", "%(count)d chambres accessibles", access.accueil_chambre_nombre_accessibles
    ) % {"count": access.accueil_chambre_nombre_accessibles}
