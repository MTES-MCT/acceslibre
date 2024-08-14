from erp.provider import arrondissements


def test_get_by_code_insee():
    assert arrondissements.get_by_code_insee("75120") is not None
    assert arrondissements.get_by_code_insee(75120) is not None
    assert arrondissements.get_by_code_insee("xxx") is None
