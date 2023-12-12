from django.utils.translation import gettext_lazy as translate_lazy

from .dataclasses import Answer


# TODO rename to "unsure" ?
def not_sure_answer(fields):
    return Answer(
        label=translate_lazy("Je ne suis pas sur"),
        picture="foo.jpg",
        modelisations=[{"field": field, "value": None} for field in fields],
    )


def yes_answer(fields):
    return Answer(
        label=translate_lazy("Oui"),
        picture="foo.jpg",
        modelisations=[{"field": field, "value": True} for field in fields],
    )


def no_answer(fields):
    return Answer(
        label=translate_lazy("Non"),
        picture="foo.jpg",
        modelisations=[{"field": field, "value": False} for field in fields],
    )
