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


def test_extract_etablissement_nom_empty():
    nom = sirene.extract_etablissement_nom({})

    assert nom == ""


def test_extract_etablissement_nom():
    assert "Nom1 Nom2 Nom3 Raison" == sirene.extract_etablissement_nom(
        {
            sirene.UNITE_LEGALE: {
                sirene.NOM_ENSEIGNE3: "nom3",
                sirene.RAISON_SOCIALE: "raison",
            },
            sirene.PERIODES_ETABLISSEMENT: [
                {sirene.NOM_ENSEIGNE1: "nom1", sirene.NOM_ENSEIGNE2: "nom2",}
            ],
        }
    )
    assert "Nom1 Nom2 Raison" == sirene.extract_etablissement_nom(
        {
            sirene.UNITE_LEGALE: {sirene.RAISON_SOCIALE: "raison",},
            sirene.PERIODES_ETABLISSEMENT: [
                {sirene.NOM_ENSEIGNE1: "nom1", sirene.NOM_ENSEIGNE2: "nom2",}
            ],
        }
    )
    assert "Nom1 Nom2" == sirene.extract_etablissement_nom(
        {
            sirene.UNITE_LEGALE: {},
            sirene.PERIODES_ETABLISSEMENT: [
                {sirene.NOM_ENSEIGNE1: "nom1", sirene.NOM_ENSEIGNE2: "nom2",}
            ],
        }
    )
    assert "Nom3 Raison" == sirene.extract_etablissement_nom(
        {
            sirene.UNITE_LEGALE: {
                sirene.NOM_ENSEIGNE3: "nom3",
                sirene.RAISON_SOCIALE: "raison",
            },
        }
    )
    assert "Nom Prenom" == sirene.extract_etablissement_nom(
        {
            sirene.UNITE_LEGALE: {
                sirene.PERSONNE_PRENOM: "prenom",
                sirene.PERSONNE_NOM: "nom",
            },
        }
    )
    assert "Foo B.A.R" == sirene.extract_etablissement_nom(
        {sirene.UNITE_LEGALE: {sirene.RAISON_SOCIALE: "FOO B.A.R",},}
    )
