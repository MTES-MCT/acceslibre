def entree_not_plain_pied(**kwargs):
    return kwargs["access"].entree_plain_pied is False


def has_door(**kwargs):
    return kwargs["access"].entree_porte_presence is True
