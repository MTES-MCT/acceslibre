from django.utils.translation import gettext_lazy as translate_lazy

from .dataclasses import UNIQUE_ANSWER, Answer, Question

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
not_sure = Answer(
    label=translate_lazy("Je ne suis pas sur"),
    picture="foo.jpg",
    modelisation=[{"field": "entree_plain_pied", "value": None}],
)

STEP_QUESTION = Question(
    label=translate_lazy("Y a t-il une marche (ou plus) à l'entrée de l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[at_least_one_step, no_step, not_sure],
    display_conditions=[],
)
