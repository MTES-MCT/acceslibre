from django.utils.translation import gettext_lazy as translate_lazy

from .access_utils import no_answer, not_sure_answer, yes_answer
from .conditions import has_no_parking, has_parking
from .dataclasses import UNIQUE_ANSWER, Answer, Question

PARKING_QUESTION = Question(
    label=translate_lazy("Y a-t-il un parking réservé aux visiteurs ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["stationnement_presence"]),
        no_answer(["stationnement_presence"]),
        not_sure_answer(["stationnement_presence"]),
    ],
)


PARKING_FOR_DISABLED_QUESTION = Question(
    label=translate_lazy("Y a-t-il une place PMR dans le parking ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["stationnement_pmr"]),
        no_answer(["stationnement_pmr"]),
        not_sure_answer(["stationnement_pmr"]),
    ],
    display_conditions=[has_parking],
)

parking_for_disabled = Answer(
    label=translate_lazy("Places PMR"),
    picture="1-7-b-places_pmr.jpg",
    modelisations=[
        {"field": "stationnement_ext_presence", "value": True},
        {"field": "stationnement_ext_pmr", "value": True},
    ],
)

parking_not_for_disabled = Answer(
    label=translate_lazy("Places classiques"),
    picture="1-7-b-stationnement.jpg",
    modelisations=[
        {"field": "stationnement_ext_presence", "value": True},
        {"field": "stationnement_ext_pmr", "value": False},
    ],
)

no_parking = Answer(
    label=translate_lazy("Pas de parking"),
    picture="cross.png",
    modelisations=[
        {"field": "stationnement_ext_presence", "value": False},
        {"field": "stationnement_ext_pmr", "value": False},
    ],
)

PARKING_FOR_DISABLED_NEARBY_QUESTION = Question(
    label=translate_lazy("Y a-t-il des places de stationnement PMR dans les environs (200 mètres) ?"),
    type=UNIQUE_ANSWER,
    answers=[
        parking_for_disabled,
        parking_not_for_disabled,
        no_parking,
        not_sure_answer(["stationnement_ext_presence", "stationnement_ext_pmr"]),
    ],
    display_conditions=[has_no_parking],
)
