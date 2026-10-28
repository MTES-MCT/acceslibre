import re

from django.conf import settings
from magic_profanity import ProfanityFilter

# Harmless compound words whose parts must not be matched individually.
# magic_profanity splits text on non-alphanumeric characters (the hyphen
# included), so "pique-nique" is seen as "pique" + "nique", and "nique" is a
# standalone entry of the French wordlist. Masking these compounds keeps the
# standalone word blocked while allowing the compound.
ALLOWED_COMPOUND_PATTERNS = (r"pique[\s\-]+niques?",)

_ALLOWED_COMPOUND_RE = re.compile(
    r"(?<!\w)(?:%s)(?!\w)" % "|".join(ALLOWED_COMPOUND_PATTERNS),
    re.IGNORECASE,
)


def get_profanity_filter() -> ProfanityFilter:
    profanity_filter = ProfanityFilter()
    profanity_filter.load_words_from_file(settings.FRENCH_PROFANITY_WORDLIST)
    return profanity_filter


def contains_profanity(text: str, profanity_filter: ProfanityFilter | None = None) -> bool:
    if not text:
        return False
    if profanity_filter is None:
        profanity_filter = get_profanity_filter()
    sanitized_text = _ALLOWED_COMPOUND_RE.sub(" ", text)
    return profanity_filter.has_profanity(sanitized_text)
