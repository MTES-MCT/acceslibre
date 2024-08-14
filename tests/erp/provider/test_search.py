from erp.provider import search


def test_search_sort_and_filter():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"siret": "1", "code_insee": "42000", "coordonnees": [1, 1]},
            {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
            {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
            {"siret": "3", "code_insee": "11000", "coordonnees": None},
            {"siret": "4", "code_insee": "34170", "coordonnees": [1, 1]},
            {"siret": "5", "code_insee": "34270", "coordonnees": None},
            {"siret": None, "code_insee": "34830", "coordonnees": [1, 1]},
        ],
    )

    assert results == [
        # duplicate not included
        {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
        # erp can have missing siret
        {"siret": None, "code_insee": "34830", "coordonnees": [1, 1]},
        # erp in same departement included
        {"siret": "4", "code_insee": "34170", "coordonnees": [1, 1]},
    ]


def test_search_sort_and_filter_exclude_non_geolocalized():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"siret": "1", "code_insee": "42000", "coordonnees": None},
            {"siret": "2", "code_insee": "34830", "coordonnees": None},
        ],
    )

    assert results == []


def test_search_sort_and_filter_exclude_other_departments():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"siret": "1", "code_insee": "42000", "coordonnees": [1, 1]},
            {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
        ],
    )

    assert results == [
        {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
    ]


def test_search_sort_and_filter_exclude_sort_by_target_code_insee():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"siret": "1", "code_insee": "34170", "coordonnees": [1, 1]},
            {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
        ],
    )

    assert results == [
        {"siret": "2", "code_insee": "34830", "coordonnees": [1, 1]},
        {"siret": "1", "code_insee": "34170", "coordonnees": [1, 1]},
    ]


def test_search_sort_and_filter_exclude_dedupe():
    results = search.sort_and_filter_results(
        "34830",
        [
            {"siret": "1", "code_insee": "34170", "coordonnees": [1, 1]},
            {"siret": "1", "code_insee": "34170", "coordonnees": [2, 2]},
        ],
    )

    assert results == [
        {"siret": "1", "code_insee": "34170", "coordonnees": [1, 1]},
    ]
