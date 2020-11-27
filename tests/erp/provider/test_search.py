import pytest

from erp.models import Commune, Erp
from erp.provider import search


def test_find_public_types_simple():
    assert search.find_public_types("dlfhsdjhfsjh") == []
    assert (
        search.find_public_types("Commissariat de police")[0] == "commissariat_police"
    )
    assert search.find_public_types("commissariat")[0] == "commissariat_police"
    assert search.find_public_types("maison du handicap")[0] == "maison_handicapees"
    assert search.find_public_types("MDPH hérault")[0] == "maison_handicapees"
    assert search.find_public_types("protection enfant")[0] == "pmi"
    assert search.find_public_types("ASSEDIC castelnau le lez")[0] == "pole_emploi"
    assert search.find_public_types("préfécture à paris")[0] == "prefecture"
    assert search.find_public_types("sous prefecture")[0] == "sous_pref"
    assert (
        search.find_public_types("accompagnement gériatrie")[0]
        == "accompagnement_personnes_agees"
    )

    assert search.find_public_types("information logement")[0] == "adil"
    assert search.find_public_types("formation pro")[0] == "afpa"
    assert search.find_public_types("ARS rhone")[0] == "ars_antenne"
    assert search.find_public_types("aide aux victimes")[0] == "bav"
    assert search.find_public_types("service civique")[0] == "bsn"
    assert search.find_public_types("cour d'appel")[0] == "cour_appel"
    assert search.find_public_types("cci montpellier")[0] == "cci"
    assert search.find_public_types("droits des femmes")[0] == "cidf"


def test_find_public_types_multiple():
    prisons = search.find_public_types("prison de fresnes")
    assert "centre_penitentiaire" in prisons
    assert "centre_detention" in prisons
    assert "maison_arret" in prisons

    impots = search.find_public_types("impots")
    assert "centre_impots_fonciers" in impots
    assert "sie" in impots
    assert "sip" in impots
    assert "urssaf" in impots

    tribunaux = search.find_public_types("tribunal")
    assert "ta" in tribunaux
    assert "te" in tribunaux
    assert "tgi" in tribunaux
    assert "ti" in tribunaux
    assert "tribunal_commerce" in tribunaux


def test_search_sort_and_filter():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"code_insee": "42000", "coordonnees": [1, 1]},
            {"code_insee": "34830", "coordonnees": [1, 1]},
            {"code_insee": "11000", "coordonnees": None},
            {"code_insee": "34170", "coordonnees": [1, 1]},
            {"code_insee": "34270", "coordonnees": None},
        ],
    )

    assert results == [
        {"code_insee": "34830", "coordonnees": [1, 1]},
        {"code_insee": "34170", "coordonnees": [1, 1]},
    ]
