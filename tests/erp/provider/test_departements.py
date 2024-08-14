from erp.provider import departements


def test_get_departement():
    assert departements.get_departement("95")["nom"] == "Val-d'Oise"


def test_search_departement_empty_terms():
    assert departements.search("") == []


def test_search_departement_simple():
    assert departements.search("essonne") == [departements.get_departement("91")]


def test_search_departement_accent():
    assert departements.search("reunion") == [departements.get_departement("974")]


def test_search_departement_full_match():
    assert departements.search("haute saone")[0] == departements.get_departement("70")


def test_search_departement_partial_match():
    res = departements.search("val")

    assert departements.get_departement("94") in res
    assert departements.get_departement("95") in res


def test_search_departement_score():
    with_scores = departements.search("haute saone", keep_scores=True)

    assert with_scores[0]["score"] == 1
    assert with_scores[1]["score"] == 0.5


def test_search_departement_exclude_stopword():
    assert departements.search("territoire belfort") == [departements.get_departement("90")]


def test_search_departement_limit():
    assert len(departements.search("er")) == 12
    assert len(departements.search("er", limit=5)) == 5
