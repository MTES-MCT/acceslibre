import pytest

from erp.profanity import contains_profanity, get_profanity_filter


@pytest.fixture(scope="module")
def profanity_filter():
    return get_profanity_filter()


def test_contains_profanity_detects_standalone_word(profanity_filter):
    assert contains_profanity("nique", profanity_filter)
    assert contains_profanity("Nique !", profanity_filter)


def test_contains_profanity_ignores_allowed_compounds(profanity_filter):
    assert not contains_profanity("L'aire de pique-nique est accessible.", profanity_filter)
    assert not contains_profanity("L'aire de pique nique est accessible.", profanity_filter)
    assert not contains_profanity("Plusieurs pique-niques sont aménagés.", profanity_filter)
    assert not contains_profanity("Pique-Nique", profanity_filter)


def test_contains_profanity_still_detects_other_profanities_in_compound_sentence(profanity_filter):
    assert contains_profanity("Un pique-nique, connard.", profanity_filter)


def test_contains_profanity_detects_profane_phrase(profanity_filter):
    assert contains_profanity("nique ta mère", profanity_filter)
