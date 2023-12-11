from dataclasses import dataclass

from django.utils.safestring import mark_safe

UNIQUE_ANSWER = "unique"
UNIQUE_OR_INT_ANSWER = "unique_or_int"


@dataclass
class Question:
    label: str
    type: str
    answers: list
    display_conditions: list

    @property
    def choices(self):
        img_url = "https://placehold.it/200x200"  # TODO remove me
        return [(a.label, mark_safe(f"<img src='{img_url}' alt='{a.label}'>{a.label}")) for a in self.answers]


@dataclass
class Answer:
    label: str
    picture: str
    modelisations: list
