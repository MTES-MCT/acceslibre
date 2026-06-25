import deepl
import deepl.http_client
from django.conf import settings

deepl.http_client.min_connection_timeout = 10.0
deepl.http_client.max_network_retries = 0

_translator = deepl.Translator(settings.DEEPL_AUTH_KEY)


def translate(text: str, target_lang):
    if target_lang not in settings.DEEPL_MAPPING:
        return None

    translator = deepl.Translator(settings.DEEPL_AUTH_KEY)
    result = translator.translate_text(text, target_lang=settings.DEEPL_MAPPING[target_lang])
    try:
        result = _translator.translate_text(text, target_lang=settings.DEEPL_MAPPING[target_lang])
        return result.text if result else None
    except deepl.exceptions.DeepLException:
        return None
