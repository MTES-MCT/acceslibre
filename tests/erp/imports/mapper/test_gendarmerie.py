import pytest

from erp.imports.fetcher import StringFetcher
from erp.models import Activite, Erp
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


def test_basic_stats(import_dataset, gendarmeries_valid):
    imported, skipped, errors = import_dataset().job()
    erp = Erp.objects.filter(
        source_id=gendarmeries_valid[0]["identifiant_public_unite"]
    ).first()
    assert erp is not None
    assert erp.voie is not None
    assert (
        erp.contact_url
        == "https://www.gendarmerie.interieur.gouv.fr/a-votre-contact/contacter-la-gendarmerie/magendarmerie.fr"
    )
    assert (imported, skipped) == (3, 0)


def test_updated_data(import_dataset, gendarmeries_valid):
    import_dataset().job()

    gendarmeries_valid_updated = gendarmeries_valid.copy()
    gendarmeries_valid_updated[0]["code_commune_insee"] = "01283"
    imported, skipped, errors = import_dataset(gendarmeries_valid_updated).job()

    erp = Erp.objects.filter(
        source_id=gendarmeries_valid_updated[0]["identifiant_public_unite"]
    ).first()
    assert erp is not None
    assert erp.code_insee == gendarmeries_valid_updated[0]["code_commune_insee"]
    assert (imported, skipped) == (3, 0)


def test_invalid_data(mapper, gendarmeries_valid):
    sample = gendarmeries_valid[0].copy()
    sample["code_commune_insee"] = "67000azdasqd"

    with pytest.raises(RuntimeError) as err:
        mapper(sample).process()

    assert "résoudre la commune depuis le code INSEE" in str(err.value)


def test_fail_on_schema_change(import_dataset, gendarmeries_valid):
    gendarmeries_invalid = gendarmeries_valid[0].copy()
    gendarmeries_invalid[0]["code_insee"] = "test"
    del gendarmeries_invalid[0]["code_commune_insee"]

    imported, skipped, errors = import_dataset(gendarmeries_invalid).job()
    assert (imported, skipped) == (2, 1)


def test_horaires(import_dataset, gendarmeries_valid):
    imported, skipped, errors = import_dataset(gendarmeries_valid).job()
    assert (imported, skipped, errors) == (3, 0, [])

    erp = Erp.objects.filter(
        source_id=gendarmeries_valid[0]["identifiant_public_unite"]
    ).first()

    assert "Horaires d'accueil" in erp.accessibilite.commentaire
    assert "Lundi : 8h00-12h00 14h00-18h00" in erp.accessibilite.commentaire


def test_horaires_missing(import_dataset, gendarmeries_valid):
    imported, skipped, errors = import_dataset(gendarmeries_valid).job()
    assert (imported, skipped, errors) == (3, 0, [])

    erp = Erp.objects.filter(
        source_id=gendarmeries_valid[1]["identifiant_public_unite"]
    ).first()

    assert "Horaires d'accueil" not in erp.accessibilite.commentaire
