import pytest

from erp.models import Activite
from tests.erp.imports.mapper.fixtures import gendarmeries_valid
from erp.imports.mapper.gendarmerie import GendarmerieMapper


@pytest.fixture
def activite_gendarmerie(db):
    return Activite.objects.create(nom="Gendarmerie")


@pytest.fixture
def mapper(db, activite_gendarmerie):
    def _factory(record, today=None):
        return GendarmerieMapper(record, activite_gendarmerie, today=today)

    return _factory


def test_basic_stats(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[0].copy()
    erp, reason = mapper(sample).process()

    assert erp.code_insee == gendarmeries_valid[0]["code_commune_insee"]
    assert reason is None


def test_updated_data(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[0].copy()
    sample["code_commune_insee"] = "01283"

    erp, reason = mapper(sample).process()

    assert erp.code_insee == "01283"


def test_invalid_data(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[0].copy()
    sample["code_commune_insee"] = "67000azdasqd"

    with pytest.raises(RuntimeError) as err:
        mapper(sample).process()

    assert "résoudre la commune depuis le code INSEE" in str(err.value)


def test_fail_on_key_change(mapper, gendarmeries_valid):
    gendarmeries_invalid = gendarmeries_valid[0].copy()
    gendarmeries_invalid["code_insee"] = "test"
    del gendarmeries_invalid["code_commune_insee"]

    with pytest.raises(RuntimeError) as err:
        mapper(gendarmeries_invalid).process()

    assert "code_commune_insee" in str(err.value)


def test_horaires(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[0].copy()
    erp, reason = mapper(sample).process()

    assert "Horaires d'accueil" in erp.accessibilite.commentaire
    assert "Lundi : 8h00-12h00 14h00-18h00" in erp.accessibilite.commentaire


def test_horaires_missing(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[2].copy()
    erp, reason = mapper(sample).process()

    assert "Horaires d'accueil" not in erp.accessibilite.commentaire
