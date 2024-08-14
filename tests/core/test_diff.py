from core.lib import diff


def test_dict_diff_keys():
    x = {"a": 1, "b": 2, "c": 3}
    y = {"a": 1, "b": 3, "c": 4}

    assert diff.dict_diff_keys(x, y) == [
        {"field": "b", "new": 3, "old": 2},
        {"field": "c", "new": 4, "old": 3},
    ]
