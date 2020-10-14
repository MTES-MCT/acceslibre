import pytest

from erp.provider import sirene


def test_create_find_query_single_word():
    q = sirene.create_find_query("akei", "34830")

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:AKEI~ OR denominationUsuelle1UniteLegale:AKEI~ OR nomUniteLegale:AKEI~ OR periode(enseigne1Etablissement:AKEI~) OR periode(denominationUsuelleEtablissement:AKEI~))'
    )


def test_create_find_query_multiple_words():
    q = sirene.create_find_query("BISTRO BROOKLYN", "34830")

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:"BISTRO BROOKLYN"~ OR denominationUsuelle1UniteLegale:"BISTRO BROOKLYN"~ OR nomUniteLegale:"BISTRO BROOKLYN"~ OR periode(enseigne1Etablissement:"BISTRO BROOKLYN"~) OR periode(denominationUsuelleEtablissement:"BISTRO BROOKLYN"~))'
    )


def test_create_find_query_apostrophe():
    q = sirene.create_find_query("l'insolent", "34830")

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:"L\'INSOLENT"~ OR denominationUsuelle1UniteLegale:"L\'INSOLENT"~ OR nomUniteLegale:"L\'INSOLENT"~ OR periode(enseigne1Etablissement:"L\'INSOLENT"~) OR periode(denominationUsuelleEtablissement:"L\'INSOLENT"~))'
    )


def test_create_find_query_with_naf():
    q = sirene.create_find_query("akei", "34830", naf="32.01")

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"34830" OR libelleCommuneEtablissement:34830~) AND (denominationUniteLegale:AKEI~ OR denominationUsuelle1UniteLegale:AKEI~ OR nomUniteLegale:AKEI~ OR periode(enseigne1Etablissement:AKEI~) OR periode(denominationUsuelleEtablissement:AKEI~)) AND activitePrincipaleUniteLegale:32.01~'
    )


def test_create_find_query_commune_with_dashes():
    q = sirene.create_find_query("akei", "Vaulx-en-Velin", naf="32.01")

    assert (
        q.toURLParams()
        == 'etatAdministratifUniteLegale:A AND (codePostalEtablissement:"Vaulx-en-Velin" OR libelleCommuneEtablissement:"Vaulx-en-Velin"~) AND (denominationUniteLegale:AKEI~ OR denominationUsuelle1UniteLegale:AKEI~ OR nomUniteLegale:AKEI~ OR periode(enseigne1Etablissement:AKEI~) OR periode(denominationUsuelleEtablissement:AKEI~)) AND activitePrincipaleUniteLegale:32.01~'
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
