import pytest

from .. import sirene


def test_create_find_query_single_word():
    q = sirene.create_find_query("akei", "34830", limit=10)

    assert (
        q.toURLParams() == "codePostalEtablissement:34830 AND "
        "etatAdministratifUniteLegale:A AND "
        "(denominationUniteLegale:akei~ OR "
        "denominationUsuelle1UniteLegale:akei~ OR "
        "nomUniteLegale:akei~ OR "
        "periode(enseigne1Etablissement:akei~) "
        "OR periode(denominationUsuelleEtablissement:akei~))"
    )


def test_create_find_query_multiple_words():
    q = sirene.create_find_query("bistro brooklyn", "34830", limit=10)

    assert (
        q.toURLParams() == "codePostalEtablissement:34830 AND "
        "etatAdministratifUniteLegale:A AND "
        '(denominationUniteLegale:"bistro brooklyn"~2 OR '
        'denominationUsuelle1UniteLegale:"bistro brooklyn"~2 OR '
        'nomUniteLegale:"bistro brooklyn"~2 OR '
        'periode(enseigne1Etablissement:"bistro brooklyn"~2) OR '
        'periode(denominationUsuelleEtablissement:"bistro brooklyn"~2))'
    )
