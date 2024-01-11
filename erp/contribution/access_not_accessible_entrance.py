from django.utils.translation import gettext_lazy as translate_lazy

from ..schema import RAMPE_AUCUNE, RAMPE_FIXE
from .access_utils import no_answer, not_sure_answer, yes_answer
from .conditions import entrance_is_not_accessible, path_to_entrance_has_steps, staff_can_help
from .dataclasses import UNIQUE_ANSWER, UNIQUE_OR_INT_ANSWER, Answer, Question

CAN_STAFF_HELP_QUESTION = Question(
    label=translate_lazy("A l'entrée, y a-t-il du personnel pouvant aider une personne à mobilité réduite si besoin ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["entree_aide_humaine"]),
        no_answer(["entree_aide_humaine"]),
        not_sure_answer(["entree_aide_humaine"]),
    ],
    display_conditions=[entrance_is_not_accessible],
)

CALL_STAFF_EQUIPMENT_QUESTION = Question(
    label=translate_lazy(
        "Y a-t-il une sonnette ou un dispositif d'appel permettant de signaler sa présence à l'entrée ?"
    ),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["entree_dispositif_appel"]),
        no_answer(["entree_dispositif_appel"]),
        not_sure_answer(["entree_dispositif_appel"]),
    ],
    display_conditions=[entrance_is_not_accessible, staff_can_help],
)

SPECIFIC_ENTRANCE_QUESTION = Question(
    label=translate_lazy("Y a-t-il une entrée dédiée aux personnes à mobilité réduite ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["entree_pmr"]),
        no_answer(["entree_pmr"]),
        not_sure_answer(["entree_pmr"]),
    ],
    display_conditions=[entrance_is_not_accessible],
)

RECEPTION_NEAR_ENTRANCE_QUESTION = Question(
    label=translate_lazy("L'accueil, est-il à proximité immédiate de l'entrée ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_visibilite"]),
        no_answer(["accueil_visibilite"]),
        not_sure_answer(["accueil_visibilite"]),
    ],
    display_conditions=[entrance_is_not_accessible],
)

PATH_TO_RECEPTION_QUESTION = Question(
    label=translate_lazy("Le chemin jusqu'à l'accueil est-il de plain pied c'est-à-dire sans marche ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_cheminement_plain_pied"]),
        no_answer(["accueil_cheminement_plain_pied"]),
        not_sure_answer(["accueil_cheminement_plain_pied"]),
    ],
    display_conditions=[entrance_is_not_accessible],
)

PATH_TO_RECEPTION_STEPS_QUESTION = Question(
    label=translate_lazy("Combien de marches y a-t-il pour se rendre à l'accueil ?"),
    type=UNIQUE_OR_INT_ANSWER,
    answers=[not_sure_answer(["accueil_cheminement_nombre_marches"])],
    display_conditions=[entrance_is_not_accessible, path_to_entrance_has_steps],
)


no_equipment = Answer(
    label=translate_lazy("Ni rampe ni ascenseur"),
    picture="2-8-c_escalier_sans_rien.jpg",
    modelisations=[
        {"field": "accueil_cheminement_rampe", "value": RAMPE_AUCUNE},
        {"field": "accueil_cheminement_ascenseur", "value": False},
    ],
)


elevator = Answer(
    label=translate_lazy("Ascenceur ou élévateur"),
    picture="2-8-c-elevateur.jpg",
    modelisations=[
        {"field": "accueil_cheminement_rampe", "value": RAMPE_AUCUNE},
        {"field": "accueil_cheminement_ascenseur", "value": True},
    ],
)

ramp = Answer(
    label=translate_lazy("Rampe"),
    picture="2-8-c-rampe.jpg",
    modelisations=[
        {"field": "accueil_cheminement_rampe", "value": RAMPE_FIXE},
        {"field": "accueil_cheminement_ascenseur", "value": False},
    ],
)
both_equipments = Answer(
    label=translate_lazy("Les 2 : Rampe et ascenceur / élévateur"),
    picture="1-1-c_deux_equipements.jpg",
    modelisations=[
        {"field": "accueil_cheminement_rampe", "value": RAMPE_FIXE},
        {"field": "accueil_cheminement_ascenseur", "value": True},
    ],
)

PATH_TO_RECEPTION_STEPS_EQUIPMENT_QUESTION = Question(
    label=translate_lazy("Y a-t-il un ascenseur ou une rampe permettant de franchir ces marches ?"),
    type=UNIQUE_ANSWER,
    answers=[
        no_equipment,
        elevator,
        ramp,
        both_equipments,
        not_sure_answer(["accueil_cheminement_rampe", "accueil_cheminement_ascenseur"]),
    ],
    display_conditions=[entrance_is_not_accessible, path_to_entrance_has_steps],
)
