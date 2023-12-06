from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import ESCALIER_DESCENDANT, ESCALIER_MONTANT, RAMPE_AMOVIBLE, RAMPE_AUCUNE, RAMPE_FIXE

from .dataclasses import UNIQUE_ANSWER, UNIQUE_OR_INT_ANSWER, Answer, Question


def _not_sure_answer(field):
    return Answer(
        label=translate_lazy("Je ne suis pas sur"),
        picture="foo.jpg",
        modelisation=[{"field": field, "value": None}],
    )


at_least_one_step = Answer(
    label=translate_lazy("Une marche ou plus"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_plain_pied", "value": False}],
)
no_step = Answer(
    label=translate_lazy("Pas de marche"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_plain_pied", "value": True}],
)


STEP_QUESTION = Question(
    label=translate_lazy("Y a t-il une marche (ou plus) à l'entrée de l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[at_least_one_step, no_step, _not_sure_answer("entree_plain_pied")],
    display_conditions=[],
)

# TODO how to handle the int case here ?
STEP_NUMBER_QUESTION = Question(
    label=translate_lazy("Combien de marches y a-t-il pour entrer dans l'établissement ?"),
    type=UNIQUE_OR_INT_ANSWER,
    answers=[_not_sure_answer("entree_marches")],
    # TODO write me
    display_conditions=["entree_plain_pied_is_false"],
)

stairs_up = Answer(
    label=translate_lazy("Monter"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_marches_sens", "value": ESCALIER_MONTANT}],
)
stairs_down = Answer(
    label=translate_lazy("Descendre"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_marches_sens", "value": ESCALIER_DESCENDANT}],
)

STEP_DIRECTION_QUESTION = Question(
    label=translate_lazy("Faut-il monter ou descendre les marches pour atteindre l'entrée ?"),
    type=UNIQUE_ANSWER,
    answers=[stairs_up, stairs_down, _not_sure_answer("entree_marches_sens")],
    display_conditions=["entree_plain_pied_is_false"],
)


fixed_ramp = Answer(
    label=translate_lazy("Rampe fixe"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_marches_rampe", "value": RAMPE_FIXE}],
)
movable_ramp = Answer(
    label=translate_lazy("Rampe amovible"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_marches_rampe", "value": RAMPE_AMOVIBLE}],
)

no_ramp = Answer(
    label=translate_lazy("Pas de rampe"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_marches_rampe", "value": RAMPE_AUCUNE}],
)


STEP_RAMP_QUESTION = Question(
    label=translate_lazy("Avez-vous une rampe d'accès pour entrer dans l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[fixed_ramp, movable_ramp, no_ramp, _not_sure_answer("entree_marches_rampe")],
    display_conditions=["entree_plain_pied_is_false"],
)
