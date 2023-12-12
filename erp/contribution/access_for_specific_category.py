from django.utils.translation import gettext_lazy as translate_lazy

from erp.schema import (
    EQUIPEMENT_MALENTENDANT_BIM,
    EQUIPEMENT_MALENTENDANT_BM_PORTATIVE,
    EQUIPEMENT_MALENTENDANT_LPC,
    EQUIPEMENT_MALENTENDANT_LSF,
    EQUIPEMENT_MALENTENDANT_STS,
)

from .access_utils import no_answer, not_sure_answer, yes_answer
from .dataclasses import UNIQUE_ANSWER, Answer, Question

# TODO
# ROOM_QUESTION = Question(
#     label=translate_lazy("Dans votre établissement, y a-t-il des chambres PMR ?"),
#     type=UNIQUE_ANSWER,
#     answers=[toilets_with_access, toilets_without_access, no_toilets, not_sure_answer(["sanitaires_presence", "sanitaires_adaptes"])],
#     display_conditions=[],
# )

# TODO add question on the number of rooms

HEARING_EQUIPMENT_QUESTION = Question(
    label=translate_lazy("A l'accueil, y a-t-il un équipement pour les personnes sourdes ou malentendantes ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_equipements_malentendants_presence"]),
        no_answer(["accueil_equipements_malentendants_presence"]),
        not_sure_answer(["accueil_equipements_malentendants_presence"]),
    ],
    display_conditions=["is_cultural_place"],
)

fixed_bim = Answer(
    label=translate_lazy("Boucle à induction magnétique fixe"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": EQUIPEMENT_MALENTENDANT_BIM},
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
        {"field": "accueil_equipements_malentendants", "value": EQUIPEMENT_MALENTENDANT_LSF},
    ],
)
lfpc = Answer(
    label=translate_lazy("Langue française parlée complétée (LFPC)"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": EQUIPEMENT_MALENTENDANT_LPC},
    ],
)
subtitles = Answer(
    label=translate_lazy("Sous titrage ou transcription simultanée"),
    picture="foo.jpg",
    modelisations=[
        {"field": "accueil_equipements_malentendants", "value": EQUIPEMENT_MALENTENDANT_STS},
    ],
)

HEARING_EQUIPMENT_TYPE_QUESTION = Question(
    label=translate_lazy("A l'accueil, y a-t-il un équipement pour les personnes sourdes ou malentendantes ?"),
    type=UNIQUE_ANSWER,
    answers=[fixed_bim, removable_bim, lsf, lfpc, subtitles, not_sure_answer(["accueil_equipements_malentendants"])],
    display_conditions=["is_cultural_place", "has_hearing_equipment"],
)


AUDIODESCRIPTION_QUESTION = Question(
    label=translate_lazy("L'établissement propose-t-il de l'audiodescription ?"),
    type=UNIQUE_ANSWER,
    answers=[
        yes_answer(["accueil_audiodescription_presence"]),
        no_answer(["accueil_audiodescription_presence"]),
        not_sure_answer(["accueil_audiodescription_presence"]),
    ],
    display_conditions=["is_cultural_place"],
)

# TODO missing question here
# AUDIODESCRIPTION_TYPE_QUESTION = Question(
#     label=translate_lazy("L'audiodescription est disponible grâce à :"),
#     type=UNIQUE_ANSWER,
#     answers=[yes_answer(["accueil_audiodescription_presence"]), no_answer(["accueil_audiodescription_presence"]), not_sure_answer(["accueil_audiodescription_presence"])],
#     display_conditions=["has_audiodescription"],
# )
