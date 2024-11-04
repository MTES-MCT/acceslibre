import pytest
from django.contrib.gis.geos import Point

from erp.imports.mapper.gendarmerie import GendarmerieMapper
from erp.models import Activite, Erp, ExternalSource
from tests.erp.imports.mapper.fixtures import gendarmeries_valid

_ = gendarmeries_valid  # Hack to avoid removal of the "unused" import


@pytest.fixture
def activite_gendarmerie(db):
    return Activite.objects.create(nom="Gendarmerie")


@pytest.fixture
def mapper(db, activite_gendarmerie):
    def _factory(record, today=None):
        return GendarmerieMapper(record, activite_gendarmerie, today=today)

    return _factory


def test_basic_stats(mapper, gendarmeries_valid):  # noqa
    sample = gendarmeries_valid[0].copy()
    erp, reason = mapper(sample).process()

    assert erp.code_insee == gendarmeries_valid[0]["code_commune_insee"]
    assert reason is None


def test_updated_data(mapper, gendarmeries_valid):  # noqa
    sample = gendarmeries_valid[0].copy()
    sample["code_commune_insee"] = "01283"

    erp, _ = mapper(sample).process()

    assert erp.code_insee == "01283"


def test_invalid_data(mapper, gendarmeries_valid):  # noqa
    sample = gendarmeries_valid[0].copy()
    sample["code_commune_insee"] = sample["code_postal"] = "67000azdasqd"

    with pytest.raises(RuntimeError) as err:
        mapper(sample).process()

    assert "Impossible de résoudre la commune depuis le code INSEE" in str(err.value)


def test_fail_on_key_change(mapper, gendarmeries_valid):  # noqa
    gendarmeries_invalid = gendarmeries_valid[0].copy()
    gendarmeries_invalid["code_insee"] = "test"
    del gendarmeries_invalid["code_commune_insee"]

    with pytest.raises(RuntimeError) as err:
        mapper(gendarmeries_invalid).process()

    assert "code_commune_insee" in str(err.value)


def test_horaires(mapper, gendarmeries_valid):  # noqa
    sample = gendarmeries_valid[0].copy()
    erp, _ = mapper(sample).process()

    assert "Horaires d'accueil" in erp.accessibilite.commentaire
    assert "Lundi : 8h00-12h00 14h00-18h00" in erp.accessibilite.commentaire


def test_horaires_missing(mapper, gendarmeries_valid):  # noqa
    sample = gendarmeries_valid[2].copy()
    erp, _ = mapper(sample).process()

    assert "Horaires d'accueil" not in erp.accessibilite.commentaire


def test_unpublish_preexisting_duplicate_import(mapper, activite_gendarmerie, gendarmeries_valid):  # noqa
    # create two duplicates
    preexisting = Erp.objects.create(
        nom="preexisting",
        activite=activite_gendarmerie,
        geom=Point(6.09523, 46.27591),
        published=True,
    )
    already_imported = Erp.objects.create(
        nom="already imported",
        activite=activite_gendarmerie,
        source=ExternalSource.SOURCE_GENDARMERIE,
        source_id="1008620",
        geom=Point(6.09523, 46.27591),
        published=True,
    )

    sample = gendarmeries_valid[0].copy()
    erp, _ = mapper(sample).process()

    erp.refresh_from_db()
    assert erp.pk == preexisting.pk
    assert erp.published is True

    already_imported.refresh_from_db()
    assert already_imported.published is False
