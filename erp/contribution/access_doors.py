from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import (
    PORTE_MANOEUVRE_BATTANTE,
    PORTE_MANOEUVRE_COULISSANTE,
    PORTE_MANOEUVRE_TAMBOUR,
    PORTE_MANOEUVRE_TOURNIQUET,
    PORTE_TYPE_AUTOMATIQUE,
    PORTE_TYPE_MANUELLE,
)

from .access_utils import not_sure_answer
from .dataclasses import UNIQUE_ANSWER, Answer, Question

porte_battante = Answer(
    label=translate_lazy("Porte battante"),
    picture="foo.jpg",
    modelisations=[
        {"field": "entree_porte_presence", "value": True},
        {"field": "entree_porte_manoeuvre", "value": PORTE_MANOEUVRE_BATTANTE},
    ],
)
porte_coulissante = Answer(
    label=translate_lazy("Porte coulissante"),
    picture="foo.jpg",
    modelisations=[
        {"field": "entree_porte_presence", "value": True},
        {"field": "entree_porte_manoeuvre", "value": PORTE_MANOEUVRE_COULISSANTE},
    ],
)

porte_tambour = Answer(
    label=translate_lazy("Porte tambour"),
    picture="foo.jpg",
    modelisations=[
        {"field": "entree_porte_presence", "value": True},
        {"field": "entree_porte_manoeuvre", "value": PORTE_MANOEUVRE_TAMBOUR},
    ],
)
tourniquet = Answer(
    label=translate_lazy("Porte tambour"),
    picture="foo.jpg",
    modelisations=[
        {"field": "entree_porte_presence", "value": True},
        {"field": "entree_porte_manoeuvre", "value": PORTE_MANOEUVRE_TOURNIQUET},
    ],
)

no_door = Answer(
    label=translate_lazy("Pas de porte"),
    picture="foo.jpg",
    modelisations=[{"field": "entree_porte_presence", "value": False}],
)

unsure = Answer(
    label=translate_lazy("Pas de porte"),
    picture="foo.jpg",
    modelisations=[
        {"field": "entree_porte_presence", "value": None},
        {"field": "entree_porte_manoeuvre", "value": None},
    ],
)

DOOR_QUESTION = Question(
    label=translate_lazy("De quel type est la porte d'entrée ?"),
    type=UNIQUE_ANSWER,
    answers=[porte_battante, porte_coulissante, porte_tambour, tourniquet, unsure],
    display_conditions=[],
)


automatic = Answer(
    label=translate_lazy("Porte automatique"),
    picture="foo.jpg",
    modelisations=[{"field": "entree_porte_type", "value": PORTE_TYPE_AUTOMATIQUE}],
)
manual = Answer(
    label=translate_lazy("Porte manuelle"),
    picture="foo.jpg",
    modelisations=[{"field": "entree_porte_type", "value": PORTE_TYPE_MANUELLE}],
)

DOOR_TYPE_QUESTION = Question(
    label=translate_lazy("De quel type est la porte d'entrée ?"),
    type=UNIQUE_ANSWER,
    answers=[
        automatic,
        manual,
        not_sure_answer(
            [
                "entree_porte_type",
            ]
        ),
    ],
    display_conditions=["has_door"],
)

large_door = Answer(
    label=translate_lazy("Oui"),
    picture="foo.jpg",
    modelisations=[{"field": "entree_largeur_mini", "value": 80}],
)

small_door = Answer(
    label=translate_lazy("Non"),
    picture="foo.jpg",
    modelisations=[{"field": "entree_largeur_mini", "value": 75}],
)


DOOR_SIZE_QUESTION = Question(
    label=translate_lazy(
        "La porte est-elle assez large pour le passage d'un fauteuil roulant ou d'une poussette ? (supérieur à 80cm)"
    ),
    type=UNIQUE_ANSWER,
    answers=[
        large_door,
        small_door,
        not_sure_answer(["entree_largeur_mini"]),
    ],
    display_conditions=["has_door"],
)
