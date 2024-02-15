from django.utils.translation import gettext_lazy as translate_lazy

from .dataclasses import Answer

UNSURE_ANSWER = translate_lazy("Je ne suis pas sûr(e)")


def not_sure_answer(fields):
    return Answer(
        label=UNSURE_ANSWER,
        picture="question.png",
        modelisations=[{"field": field, "value": None} for field in fields],
    )


def yes_answer(fields):
    return Answer(
        label=translate_lazy("Oui"),
        picture="check.png",
        modelisations=[{"field": field, "value": True} for field in fields],
    )


def no_answer(fields):
    return Answer(
        label=translate_lazy("Non"),
        picture="cross.png",
        modelisations=[{"field": field, "value": False} for field in fields],
    )
