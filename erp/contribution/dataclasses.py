from dataclasses import dataclass

UNIQUE_ANSWER = "unique"


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
