from dataclasses import dataclass, field

from django.utils.safestring import mark_safe

UNIQUE_ANSWER = "unique"
UNIQUE_OR_INT_ANSWER = "unique_or_int"


@dataclass
class Question:
    label: str
    type: str
    answers: list
    display_conditions: list = field(default_factory=list)

    @property
    def choices(self):
        img_url = "https://placehold.it/200x200"  # TODO remove me
        return [(a.label, mark_safe(f"<img src='{img_url}' alt='{a.label}'>{a.label}")) for a in self.answers]

    @property
    def is_unique_type(self):
        return self.type == UNIQUE_ANSWER

    @property
    def is_unique_or_int_type(self):
        return self.type == UNIQUE_OR_INT_ANSWER


@dataclass
class Answer:
    label: str
    picture: str
    modelisations: list
