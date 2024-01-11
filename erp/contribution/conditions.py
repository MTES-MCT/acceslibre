from erp.schema import PORTE_MANOEUVRE_TAMBOUR, PORTE_MANOEUVRE_TOURNIQUET, RAMPE_AUCUNE


def entree_not_plain_pied(**kwargs):
    return kwargs["access"].entree_plain_pied is False


def has_door(**kwargs):
    return kwargs["access"].entree_porte_presence is True


def has_parking(**kwargs):
    return kwargs["access"].stationnement_presence is True


def has_no_parking(**kwargs):
    return kwargs["access"].stationnement_presence is False


def has_hearing_equipment(**kwargs):
    return kwargs["access"].accueil_equipements_malentendants_presence is True


def is_cultural_place(**kwargs):
    return kwargs["erp"].is_cultural_place


def has_audiodescription(**kwargs):
    return kwargs["access"].accueil_audiodescription_presence is True


def has_at_least_one_room(**kwargs):
    rooms = kwargs["access"].accueil_chambre_nombre_accessibles
    return rooms and rooms >= 1


def has_outside_path(**kwargs):
    return kwargs["access"].cheminement_ext_presence is True


def has_outside_steps(**kwargs):
    return kwargs["access"].cheminement_ext_plain_pied is False


def entrance_is_not_accessible(**kwargs):
    if kwargs["access"].entree_porte_manoeuvre in (PORTE_MANOEUVRE_TAMBOUR, PORTE_MANOEUVRE_TOURNIQUET):
        return True

    if kwargs["access"].entree_largeur_mini and kwargs["access"].entree_largeur_mini < 80:
        return True

    entrance_not_leveled = kwargs["access"].entree_plain_pied is False
    no_elevator = kwargs["access"].entree_ascenseur is not True
    no_ramp = kwargs["access"].entree_marches_rampe in (None, RAMPE_AUCUNE)

    if entrance_not_leveled and no_elevator and no_ramp:
        return True

    return False


def accommodation_and_owner(**kwargs):
    return kwargs["erp"].was_created_by_business_owner and kwargs["erp"].is_accommodation


def is_accommodation(**kwargs):
    return kwargs["erp"].is_accommodation


def staff_can_help(**kwargs):
    return kwargs["access"].entree_aide_humaine is True


def path_to_entrance_has_steps(**kwargs):
    return kwargs["access"].accueil_cheminement_plain_pied is False
