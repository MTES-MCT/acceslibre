from dataclasses import dataclass, field

from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as translate_lazy

UNIQUE_ANSWER = "unique"
MUTIPLE_ANSWERS = "multiple"
UNIQUE_OR_INT_ANSWER = "unique_or_int"
FREE_TEXT_ANSWER = "free_text"


@dataclass
class Question:
    label: str
    type: str
    answers: list
    display_conditions: list = field(default_factory=list)

    @property
    def choices(self):
        return [
            (
                a.label,
                mark_safe(
                    f"""
        <label class="fr-label" for="id_question_{i}">{a.label}</label>
        <div class="fr-radio-rich__img fr-xl-radio-rich__img">{a.image_tag}</div>
        """
                ),
            )
            for i, a in enumerate(self.answers)
        ]
        return [(a.label, mark_safe(f"{a.image_tag}{a.label}")) for a in self.answers]

    @property
    def is_unique_type(self):
        return self.type == UNIQUE_ANSWER

    @property
    def is_unique_or_int_type(self):
        return self.type == UNIQUE_OR_INT_ANSWER

    @property
    def is_mutiple_type(self):
        return self.type == MUTIPLE_ANSWERS

    @property
    def is_free_text_type(self):
        return self.type == FREE_TEXT_ANSWER

    @property
    def free_text_field(self):
        return "commentaire"


@dataclass
class Answer:
    label: str
    picture: str
    modelisations: list

    @property
    def image_tag(self):
        path = f"img/contrib_v2/{self.picture}"
        alt = (
            translate_lazy("Je ne suis pas sûr")
            if self.label == translate_lazy("Je ne suis pas sûr(e)")
            else self.label
        )
        return f"<img src='{static(path)}' alt='{alt}'>"
