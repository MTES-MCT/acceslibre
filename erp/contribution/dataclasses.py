from dataclasses import dataclass

UNIQUE_ANSWER = "unique"
UNIQUE_OR_INT_ANSWER = "unique_or_int"


@dataclass
class Question:
    label: str
    type: str
    answers: list
    display_conditions: list


@dataclass
class Answer:
    label: str
    picture: str
    modelisation: list
