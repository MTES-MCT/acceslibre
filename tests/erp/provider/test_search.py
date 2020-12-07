import pytest

from erp.provider import search


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
