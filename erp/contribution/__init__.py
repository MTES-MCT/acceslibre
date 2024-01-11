from .access_accomodation_owner import (
    ROOM_NUMBER_QUESTION,
    ROOM_TOILET_QUESTION,
    SHOWER_QUESTION,
    SPECIFIC_ALERT_QUESTION,
    SPECIFIC_SUPPORT_QUESTION,
)
from .access_doors import DOOR_QUESTION, DOOR_SIZE_QUESTION, DOOR_TYPE_QUESTION
from .access_for_specific_category import (
    AUDIODESCRIPTION_QUESTION,
    AUDIODESCRIPTION_TYPE_QUESTION,
    HEARING_EQUIPMENT_QUESTION,
    HEARING_EQUIPMENT_TYPE_QUESTION,
    NUMBER_OF_ROOMS_QUESTION,
    ROOM_QUESTION,
)
from .access_misc import FREE_COMMENT_QUESTION, TEAM_TRAINING_QUESTION, TOILETS_QUESTION
from .access_not_accessible_entrance import (
    CALL_STAFF_EQUIPMENT_QUESTION,
    CAN_STAFF_HELP_QUESTION,
    PATH_TO_RECEPTION_QUESTION,
    PATH_TO_RECEPTION_STEPS_EQUIPMENT_QUESTION,
    PATH_TO_RECEPTION_STEPS_QUESTION,
    RECEPTION_NEAR_ENTRANCE_QUESTION,
    SPECIFIC_ENTRANCE_QUESTION,
)
from .access_outside import (
    OUTSIDE_PATH_HAS_STEPS_QUESTION,
    OUTSIDE_PATH_QUESTION,
    OUTSIDE_STEP_NUMBER_QUESTION,
    OUTSIDE_STEPS_EQUIPMENT_QUESTION,
    PUBLIC_TRANSPORT_QUESTION,
)
from .access_parking import PARKING_FOR_DISABLED_NEARBY_QUESTION, PARKING_FOR_DISABLED_QUESTION, PARKING_QUESTION
from .access_steps import STEP_DIRECTION_QUESTION, STEP_NUMBER_QUESTION, STEP_QUESTION, STEP_RAMP_QUESTION
from .exceptions import ContributionStopIteration

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


ADDITIONAL_CONTRIBUTION_QUESTIONS = [
    PUBLIC_TRANSPORT_QUESTION,
    OUTSIDE_PATH_QUESTION,
    OUTSIDE_PATH_HAS_STEPS_QUESTION,
    OUTSIDE_STEP_NUMBER_QUESTION,
    OUTSIDE_STEPS_EQUIPMENT_QUESTION,
    CAN_STAFF_HELP_QUESTION,
    CALL_STAFF_EQUIPMENT_QUESTION,
    SPECIFIC_ENTRANCE_QUESTION,
    RECEPTION_NEAR_ENTRANCE_QUESTION,
    PATH_TO_RECEPTION_QUESTION,
    PATH_TO_RECEPTION_STEPS_QUESTION,
    PATH_TO_RECEPTION_STEPS_EQUIPMENT_QUESTION,
    SHOWER_QUESTION,
    ROOM_TOILET_QUESTION,
    SPECIFIC_SUPPORT_QUESTION,
    SPECIFIC_ALERT_QUESTION,
    ROOM_NUMBER_QUESTION,
    FREE_COMMENT_QUESTION,
]


def _find_question_in_given_direction(question_number, erp, questions, offset):
    next_question_number = question_number + offset
    if next_question_number < 0:
        raise ContributionStopIteration

    while True:
        try:
            next_question = questions[next_question_number]
        except IndexError:
            raise ContributionStopIteration

        if not next_question.display_conditions:
            return next_question_number

        should_display = all([c(access=erp.accessibilite, erp=erp) for c in next_question.display_conditions])
        if should_display:
            return next_question_number

        next_question_number += offset


def get_previous_question_number(question_number, *, erp, questions):
    return _find_question_in_given_direction(question_number, erp, questions, -1)


def get_next_question_number(question_number, *, questions, erp):
    return _find_question_in_given_direction(question_number, erp, questions, +1)
