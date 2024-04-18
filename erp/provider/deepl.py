import deepl
from django.conf import settings


def translate(text: str, target_lang):
    if target_lang not in settings.DEEPL_MAPPING:
        return None

    translator = deepl.Translator(settings.DEEPL_AUTH_KEY)
    result = translator.translate_text(text, target_lang=settings.DEEPL_MAPPING[target_lang])
    return result.text if result else None
