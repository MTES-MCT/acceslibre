import erp.contribution.conditions as condition_module

from .access_doors import DOOR_QUESTION, DOOR_SIZE_QUESTION, DOOR_TYPE_QUESTION
from .access_for_specific_category import (
    AUDIODESCRIPTION_QUESTION,
    AUDIODESCRIPTION_TYPE_QUESTION,
    HEARING_EQUIPMENT_QUESTION,
    HEARING_EQUIPMENT_TYPE_QUESTION,
    NUMBER_OF_ROOMS_QUESTION,
    ROOM_QUESTION,
)
from .access_misc import TEAM_TRAINING_QUESTION, TOILETS_QUESTION
from .access_parking import PARKING_FOR_DISABLED_NEARBY_QUESTION, PARKING_FOR_DISABLED_QUESTION, PARKING_QUESTION
from .access_steps import STEP_DIRECTION_QUESTION, STEP_NUMBER_QUESTION, STEP_QUESTION, STEP_RAMP_QUESTION
from .exceptions import EndOfContributionException

CONTRIBUTION_QUESTIONS = [
    STEP_QUESTION,
    STEP_NUMBER_QUESTION,
    STEP_DIRECTION_QUESTION,
    STEP_RAMP_QUESTION,
    DOOR_QUESTION,
    DOOR_TYPE_QUESTION,
    DOOR_SIZE_QUESTION,
    TEAM_TRAINING_QUESTION,
    TOILETS_QUESTION,
    PARKING_QUESTION,
    PARKING_FOR_DISABLED_QUESTION,
    PARKING_FOR_DISABLED_NEARBY_QUESTION,
    ROOM_QUESTION,
    NUMBER_OF_ROOMS_QUESTION,
    HEARING_EQUIPMENT_QUESTION,
    HEARING_EQUIPMENT_TYPE_QUESTION,
    AUDIODESCRIPTION_QUESTION,
    AUDIODESCRIPTION_TYPE_QUESTION,
]


def get_next_question_number(question_number, *, erp):
    next_question_number = question_number + 1
    print("IN get_next_question_number")
    print(next_question_number)

    while True:
        try:
            next_question = CONTRIBUTION_QUESTIONS[next_question_number]
        except IndexError:
            raise EndOfContributionException

        if not next_question.display_conditions:
            return next_question_number

        conditions = next_question.display_conditions
        should_display = all([getattr(condition_module, c)(access=erp.accessibilite, erp=erp) for c in conditions])
        if should_display:
            return next_question_number

        next_question_number += 1
