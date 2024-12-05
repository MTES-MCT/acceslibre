from modeltranslation.translator import TranslationOptions, translator

from contact.models import FAQ


class FAQTranslation(TranslationOptions):
    fields = ("title", "description")


translator.register(FAQ, FAQTranslation)
