from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import (
    AUDIODESCRIPTION_AVEC_APP,
    AUDIODESCRIPTION_AVEC_EQUIPEMENT_OCCASIONNEL,
    AUDIODESCRIPTION_AVEC_EQUIPEMENT_PERMANENT,
    AUDIODESCRIPTION_SANS_EQUIPEMENT,
    EQUIPEMENT_MALENTENDANT_BIM,
    EQUIPEMENT_MALENTENDANT_BM_PORTATIVE,
    EQUIPEMENT_MALENTENDANT_LPC,
    EQUIPEMENT_MALENTENDANT_LSF,
    EQUIPEMENT_MALENTENDANT_STS,
)

from .access_utils import no_answer, not_sure_answer, yes_answer
from .conditions import (
    has_at_least_one_room,
    has_audiodescription,
    has_hearing_equipment,
    is_accommodation,
    is_cultural_place,
)
from .dataclasses import UNIQUE_ANSWER, UNIQUE_OR_INT_ANSWER, Answer, Question

has_rooms = Answer(
    label=translate_lazy("Oui"),
    picture="1-heberg_chambre_pmr.jpg",
    modelisations=[
        {"field": "accueil_chambre_nombre_accessibles", "value": 1},
    ],
)

no_rooms = Answer(
    label=translate_lazy("Non"),
    picture="cross.png",
    modelisations=[
        {"field": "accueil_chambre_nombre_accessibles", "value": 0},
    ],
)

ROOM_QUESTION = Question(
    label=translate_lazy("Dans cet établissement, y a-t-il des chambres PMR ?"),
    type=UNIQUE_ANSWER,
    answers=[has_rooms, no_rooms, not_sure_answer(["accueil_chambre_nombre_accessibles"])],
    display_conditions=[is_accommodation],
    easy_skip_for_screen_readers=True,
)

not_sure_number_of_rooms = Answer(
    label=translate_lazy("Je ne suis pas sûr(e)"),
    picture="question.png",
    modelisations=[
        {"field": "accueil_chambre_nombre_accessibles", "value": 1},
    ],
)

NUMBER_OF_ROOMS_QUESTION = Question(
    label=translate_lazy("Combien y a-t-il de chambres PMR ?"),
    type=UNIQUE_OR_INT_ANSWER,
    answers=[not_sure_number_of_rooms],
    display_conditions=[is_accommodation, has_at_least_one_room],
)


HEARING_EQUIPMENT_QUESTION = Question(
    label=translate_lazy("A l'accueil, y a-t-il un équipement pour les personnes sourdes ou malentendantes ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_equipements_malentendants_presence"]),
        no_answer(["accueil_equipements_malentendants_presence"]),
        not_sure_answer(["accueil_equipements_malentendants_presence"]),
    ],
    display_conditions=[is_cultural_place],
    easy_skip_for_screen_readers=True,
)

fixed_bim = Answer(
    label=translate_lazy("Boucle à induction magnétique fixe"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [EQUIPEMENT_MALENTENDANT_BIM]},
    ],
)

removable_bim = Answer(
    label=translate_lazy("Boucle à induction magnétique portative"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": EQUIPEMENT_MALENTENDANT_BM_PORTATIVE},
    ],
)
lsf = Answer(
    label=translate_lazy("Langue des signes françaises"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [EQUIPEMENT_MALENTENDANT_LSF]},
    ],
)
lfpc = Answer(
    label=translate_lazy("Langue française parlée complétée (LFPC)"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [EQUIPEMENT_MALENTENDANT_LPC]},
    ],
)
subtitles = Answer(
    label=translate_lazy("Sous titrage ou transcription simultanée"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [EQUIPEMENT_MALENTENDANT_STS]},
    ],
)

HEARING_EQUIPMENT_TYPE_QUESTION = Question(
    label=translate_lazy("A l'accueil, y a-t-il un équipement pour les personnes sourdes ou malentendantes ?"),
    type=UNIQUE_ANSWER,
    answers=[fixed_bim, removable_bim, lsf, lfpc, subtitles, not_sure_answer(["accueil_equipements_malentendants"])],
    display_conditions=[is_cultural_place, has_hearing_equipment],
    easy_skip_for_screen_readers=True,
)


AUDIODESCRIPTION_QUESTION = Question(
    label=translate_lazy("L'établissement propose-t-il de l'audiodescription ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_audiodescription_presence"]),
        no_answer(["accueil_audiodescription_presence"]),
        not_sure_answer(["accueil_audiodescription_presence"]),
    ],
    display_conditions=[is_cultural_place],
)


fixed_equipment = Answer(
    label=translate_lazy("Casques et boîtiers disponibles à l’accueil"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [AUDIODESCRIPTION_AVEC_EQUIPEMENT_PERMANENT]},
    ],
)
application = Answer(
    label=translate_lazy("Une application sur smartphone"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [AUDIODESCRIPTION_AVEC_APP]},
    ],
)
temporary_equipment = Answer(
    label=translate_lazy("Une application sur smartphone"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [AUDIODESCRIPTION_AVEC_EQUIPEMENT_OCCASIONNEL]},
    ],
)
without_equipment = Answer(
    label=translate_lazy("Aucun"),
    picture="cross.png",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": [AUDIODESCRIPTION_SANS_EQUIPEMENT]},
    ],
)

AUDIODESCRIPTION_TYPE_QUESTION = Question(
    label=translate_lazy("L'audiodescription est disponible grâce à :"),
    type=UNIQUE_ANSWER,
    answers=[
        fixed_equipment,
        application,
        temporary_equipment,
        without_equipment,
        not_sure_answer(["accueil_equipements_malentendants"]),
    ],
    display_conditions=[is_cultural_place, has_audiodescription],
)
