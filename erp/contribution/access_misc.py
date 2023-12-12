from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import PERSONNELS_AUCUN, PERSONNELS_FORMES, PERSONNELS_NON_FORMES

from .access_utils import not_sure_answer
from .dataclasses import UNIQUE_ANSWER, Answer, Question

trained_team = Answer(
    label=translate_lazy("Personnel sensibilisé"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_FORMES},
    ],
)

non_trained_team = Answer(
    label=translate_lazy("Personnel a priori non sensibilisé"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_NON_FORMES},
    ],
)

no_team = Answer(
    label=translate_lazy("Pas de personnel"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_AUCUN},
    ],
)

TEAM_TRAINING_QUESTION = Question(
    label=translate_lazy("Y a-t-il du personnel et est-il sensibilisé à l'accueil des personnes handicapées ?"),
    type=UNIQUE_ANSWER,
    answers=[trained_team, non_trained_team, no_team, not_sure_answer("accueil_personnels")],
    display_conditions=[],
)


toilets_with_access = Answer(
    label=translate_lazy("Toilettes PMR"),
    picture="foo.jpg",
    modelisations=[
        {"field": "sanitaires_presence", "value": True},
        {"field": "sanitaires_adaptes", "value": True},
    ],
)

toilets_without_access = Answer(
    label=translate_lazy("Personnel a priori non sensibilisé"),
    picture="foo.jpg",
    modelisations=[
        {"field": "sanitaires_presence", "value": True},
        {"field": "sanitaires_adaptes", "value": False},
    ],
)

no_toilets = Answer(
    label=translate_lazy("Pas de personnel"),
    picture="foo.jpg",
    modelisations=[
        {"field": "sanitaires_presence", "value": False},
        {"field": "sanitaires_adaptes", "value": False},
    ],
)


TOILETS_QUESTION = Question(
    label=translate_lazy("Y a-t-il des toilettes PMR ou non dans votre établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[
        toilets_with_access,
        toilets_without_access,
        no_toilets,
        not_sure_answer(["sanitaires_presence", "sanitaires_adaptes"]),
    ],
    display_conditions=[],
)
