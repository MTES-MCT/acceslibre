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
    return kwargs["access"].accueil_chambre_nombre_accessibles >= 1
