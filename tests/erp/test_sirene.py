import pytest

from erp import sirene


def test_create_find_query_single_word():
    q = sirene.create_find_query("akei", "34830", limit=10)

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:akei~ OR denominationUsuelle1UniteLegale:akei~ OR nomUniteLegale:akei~ OR periode(enseigne1Etablissement:akei~) OR periode(denominationUsuelleEtablissement:akei~))'
    )


def test_create_find_query_multiple_words():
    q = sirene.create_find_query("bistro brooklyn", "34830", limit=10)

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:"bistro brooklyn"~ OR denominationUsuelle1UniteLegale:"bistro brooklyn"~ OR nomUniteLegale:"bistro brooklyn"~ OR periode(enseigne1Etablissement:"bistro brooklyn"~) OR periode(denominationUsuelleEtablissement:"bistro brooklyn"~))'
    )
