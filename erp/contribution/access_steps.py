from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import ESCALIER_DESCENDANT, ESCALIER_MONTANT, RAMPE_AMOVIBLE, RAMPE_AUCUNE, RAMPE_FIXE

from .access_utils import not_sure_answer
from .conditions import entree_not_plain_pied
from .dataclasses import UNIQUE_ANSWER, UNIQUE_OR_INT_ANSWER, Answer, Question

at_least_one_step = Answer(
    label=translate_lazy("Une marche ou plus"),
    picture="1-1-a-entree_marches.jpg",
    modelisations=[{"field": "entree_plain_pied", "value": False}],
)
no_step = Answer(
    label=translate_lazy("Pas de marche"),
    picture="1-1-a-porte-sans-marche.jpg",
    modelisations=[{"field": "entree_plain_pied", "value": True}],
)


STEP_QUESTION = Question(
    label=translate_lazy("Y a t-il une marche (ou plus) à l'entrée de l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[
        at_least_one_step,
        no_step,
        not_sure_answer(["entree_plain_pied"]),
    ],
)


STEP_NUMBER_QUESTION = Question(
    label=translate_lazy("Combien de marches y a-t-il pour entrer dans l'établissement ?"),
    type=UNIQUE_OR_INT_ANSWER,
    answers=[not_sure_answer(["entree_marches"])],
    display_conditions=[entree_not_plain_pied],
)

stairs_up = Answer(
    label=translate_lazy("Monter"),
    picture="1-1-b_sens_escalier_monte.jpg",
    modelisations=[{"field": "entree_marches_sens", "value": ESCALIER_MONTANT}],
)
stairs_down = Answer(
    label=translate_lazy("Descendre"),
    picture="1-1-b_sens_escalier_descend.jpg",
    modelisations=[{"field": "entree_marches_sens", "value": ESCALIER_DESCENDANT}],
)

STEP_DIRECTION_QUESTION = Question(
    label=translate_lazy("Faut-il monter ou descendre les marches pour atteindre l'entrée ?"),
    type=UNIQUE_ANSWER,
    answers=[
        stairs_up,
        stairs_down,
        not_sure_answer(["entree_marches_sens"]),
    ],
    display_conditions=[entree_not_plain_pied],
)


fixed_ramp = Answer(
    label=translate_lazy("Rampe fixe"),
    picture="1-1-c-rampe_fixe.jpg",
    modelisations=[
        {"field": "entree_marches_rampe", "value": RAMPE_FIXE},
        {"field": "entree_ascenseur", "value": False},
    ],
)
movable_ramp = Answer(
    label=translate_lazy("Rampe amovible"),
    picture="1-1-c_rampe_amovible.jpg",
    modelisations=[
        {"field": "entree_marches_rampe", "value": RAMPE_AMOVIBLE},
        {"field": "entree_ascenseur", "value": False},
    ],
)

no_equipment = Answer(
    label=translate_lazy("Ni rampe ni ascenseur"),
    picture="cross.png",
    modelisations=[
        {"field": "entree_marches_rampe", "value": RAMPE_AUCUNE},
        {"field": "entree_ascenseur", "value": False},
    ],
)

elevator = Answer(
    label=translate_lazy("Ascenseur ou élévateur"),
    picture="1-1-c-ascenseur (2).jpg",
    modelisations=[
        {"field": "entree_marches_rampe", "value": RAMPE_AUCUNE},
        {"field": "entree_ascenseur", "value": True},
    ],
)

both_equipments = Answer(
    label=translate_lazy("Les 2 ! Rampe et Ascenseur / élévateur"),
    picture="1-1-c_deux_equipements.jpg",
    modelisations=[
        {"field": "entree_marches_rampe", "value": RAMPE_FIXE},
        {"field": "entree_ascenseur", "value": True},
    ],
)

STEP_RAMP_QUESTION = Question(
    label=translate_lazy("Avez-vous une rampe d'accès pour entrer dans l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[
        no_equipment,
        elevator,
        fixed_ramp,
        movable_ramp,
        both_equipments,
        not_sure_answer(["entree_marches_rampe", "entree_ascenseur"]),
    ],
    display_conditions=[entree_not_plain_pied],
    easy_skip_for_screen_readers=True,
)
