from modeltranslation.translator import TranslationOptions, translator

from erp.models import Activite


class ActiviteTranslation(TranslationOptions):
    fields = ("nom",)


translator.register(Activite, ActiviteTranslation)
