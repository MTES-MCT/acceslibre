from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import PERSONNELS_AUCUN, PERSONNELS_FORMES, PERSONNELS_NON_FORMES

from .access_utils import not_sure_answer
from .dataclasses import FREE_TEXT_ANSWER, UNIQUE_ANSWER, Answer, Question

trained_team = Answer(
    label=translate_lazy("Personnel sensibilisé"),
    picture="1-5-_personnel sensibilise.jpg",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_FORMES},
    ],
)

non_trained_team = Answer(
    label=translate_lazy("Personnel a priori non sensibilisé"),
    picture="1-5-_personnel non sensibilise.jpg",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_NON_FORMES},
    ],
)

no_team = Answer(
    label=translate_lazy("Pas de personnel"),
    picture="cross.png",
    modelisations=[
        {"field": "accueil_personnels", "value": PERSONNELS_AUCUN},
    ],
)

TEAM_TRAINING_QUESTION = Question(
    label=translate_lazy("Y a-t-il du personnel et est-il sensibilisé à l'accueil des personnes handicapées ?"),
    type=UNIQUE_ANSWER,
    answers=[trained_team, non_trained_team, no_team, not_sure_answer("accueil_personnels")],
    easy_skip_for_screen_readers=True,
)


toilets_with_access = Answer(
    label=translate_lazy("Toilettes PMR"),
    picture="1-6-toilettes_PMR.jpg",
    modelisations=[
        {"field": "sanitaires_presence", "value": True},
        {"field": "sanitaires_adaptes", "value": True},
    ],
)

toilets_without_access = Answer(
    label=translate_lazy("Toilettes classiques"),
    picture="1-6-toilettes_classiques.jpg",
    modelisations=[
        {"field": "sanitaires_presence", "value": True},
        {"field": "sanitaires_adaptes", "value": False},
    ],
)

no_toilets = Answer(
    label=translate_lazy("Pas de toilettes"),
    picture="cross.png",
    modelisations=[
        {"field": "sanitaires_presence", "value": False},
        {"field": "sanitaires_adaptes", "value": False},
    ],
)


TOILETS_QUESTION = Question(
    label=translate_lazy("Y a-t-il des toilettes PMR dans votre établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[
        toilets_with_access,
        toilets_without_access,
        no_toilets,
        not_sure_answer(["sanitaires_presence", "sanitaires_adaptes"]),
    ],
)

FREE_COMMENT_QUESTION = Question(
    label=translate_lazy(
        "Enfin, souhaitez vous ajouter des informations complémentaires sur l'accessibilité de cet établissement ?"
    ),
    type=FREE_TEXT_ANSWER,
    answers=[],
)
