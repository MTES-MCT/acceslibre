from django.utils.translation import gettext_lazy as translate_lazy

from .dataclasses import Answer


def not_sure_answer(field):
    return Answer(
        label=translate_lazy("Je ne suis pas sur"),
        picture="foo.jpg",
        modelisations=[{"field": field, "value": None}],
    )
