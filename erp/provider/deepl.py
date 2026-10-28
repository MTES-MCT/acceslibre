import time

import deepl
import deepl.http_client
from deepl import Translator
from django.conf import settings

deepl.http_client.min_connection_timeout = 10.0
deepl.http_client.max_network_retries = 0


def translate(text: str, target_lang):
    if target_lang not in settings.DEEPL_MAPPING:
        return None

    translator = Translator(settings.DEEPL_AUTH_KEY)
    try:
        result = translator.translate_text(text, target_lang=settings.DEEPL_MAPPING[target_lang])
        return result.text if result else None
    except deepl.exceptions.DeepLException:
        return None


class DeeplPoTranslatorService:
    """PO_TRANSLATOR_SERVICE for django-deep-translator's translate_messages command (make translate)."""

    retry_delay = 5
    max_retries = 6

    def __init__(self):
        self.translator = Translator(settings.DEEPL_AUTH_KEY)

    def translate_string(self, text, target_language, source_language="fr"):
        for attempt in range(self.max_retries + 1):
            try:
                result = self.translator.translate_text(
                    text, source_lang=source_language, target_lang=settings.DEEPL_MAPPING[target_language]
                )
                return result.text
            except deepl.exceptions.TooManyRequestsException:
                if attempt == self.max_retries:
                    raise
                time.sleep(self.retry_delay * 2**attempt)
