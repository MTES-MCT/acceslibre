from django.utils.translation import gettext_lazy as translate_lazy

from .access_utils import no_answer, not_sure_answer, yes_answer
from .conditions import has_outside_path, has_outside_steps
from .dataclasses import UNIQUE_ANSWER, UNIQUE_OR_INT_ANSWER, Answer, Question

public_transport = Answer(
    label=translate_lazy("Oui, à moins de 200m"),
    picture="foo.jpg",
    modelisations=[
        {"field": "transport_station_presence", "value": True},
    ],
)

PUBLIC_TRANSPORT_QUESTION = Question(
    label=translate_lazy("Y a-t-il des transports en commun à proximité ?"),
    type=UNIQUE_ANSWER,
    answers=[
        public_transport,
        no_answer(["transport_station_presence"]),
        not_sure_answer("transport_station_presence"),
    ],
)

no_outside_path = Answer(
    label=translate_lazy("Non, l'entrée donne directement sur la rue"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_presence", "value": False},
    ],
)

OUTSIDE_PATH_QUESTION = Question(
    label=translate_lazy("Y a-t-il un chemin privatif pour arriver à l'entrée de l'établissement ?"),
    type=UNIQUE_ANSWER,
    answers=[yes_answer(["cheminement_ext_presence"]), no_outside_path, not_sure_answer("cheminement_ext_presence")],
)

accessible_path = Answer(
    label=translate_lazy("Plain pied"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_plain_pied", "value": True},
    ],
)
not_accessible_path = Answer(
    label=translate_lazy("Une marche ou plus"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_plain_pied", "value": False},
    ],
)

OUTSIDE_PATH_HAS_STEPS_QUESTION = Question(
    label=translate_lazy("Le chemin privatif est-il de plain pied ou comporte-t-il une ou des marches ?"),
    type=UNIQUE_ANSWER,
    answers=[accessible_path, not_accessible_path, not_sure_answer("cheminement_ext_plain_pied")],
    display_conditions=[has_outside_path],
)

OUTSIDE_STEP_NUMBER_QUESTION = Question(
    label=translate_lazy("Combien de marches y a-t-il sur ce chemin d'accès ?"),
    type=UNIQUE_OR_INT_ANSWER,
    answers=[not_sure_answer(["cheminement_ext_nombre_marches"])],
    display_conditions=[has_outside_path, has_outside_steps],
)

no_equipment = Answer(
    label=translate_lazy("Non, ni rampe, ni ascenseur"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_rampe", "value": False},
        {"field": "cheminement_ext_ascenseur", "value": False},
    ],
)

elevator = Answer(
    label=translate_lazy("Ascenseur ou élévateur"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_rampe", "value": False},
        {"field": "cheminement_ext_ascenseur", "value": True},
    ],
)
ramp = Answer(
    label=translate_lazy("Rampe"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_rampe", "value": True},
        {"field": "cheminement_ext_ascenseur", "value": False},
    ],
)
both_equipements = Answer(
    label=translate_lazy("Les 2 : rampes et ascenseur ou élévateur"),
    picture="foo.jpg",
    modelisations=[
        {"field": "cheminement_ext_rampe", "value": True},
        {"field": "cheminement_ext_ascenseur", "value": True},
    ],
)

OUTSIDE_STEPS_EQUIPMENT_QUESTION = Question(
    label=translate_lazy("Y a-t-il un ascenseur ou une rampe permettant de franchir ces marches ?"),
    type=UNIQUE_ANSWER,
    answers=[
        no_equipment,
        elevator,
        ramp,
        both_equipements,
        not_sure_answer(["cheminement_ext_rampe", "cheminement_ext_ascenseur"]),
    ],
    display_conditions=[has_outside_path, has_outside_steps],
)

# TODO mossiing = Quelles sont les caractéristiques du chemin privatif ?
