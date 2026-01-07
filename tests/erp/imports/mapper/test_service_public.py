from datetime import datetime

import pytest

from erp.imports.mapper.service_public import ServicePublicMapper
from erp.models import ExternalSource
from tests.erp.imports.mapper.fixtures import service_public_valid
from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory

_ = service_public_valid  # Hack to avoid removal of the "unused" import


@pytest.fixture
def mapper(db):
    def _factory(record, today=None):
        return ServicePublicMapper(record, source=ExternalSource.SOURCE_SERVICE_PUBLIC, today=today)

    return _factory


def test_init(mapper):
    assert mapper({}).process() == (None, [], None)


def test_save_non_existing_erp(mapper, service_public_valid):  # noqa
    CommuneFactory(nom="Fontaine-le-Port")
    ActiviteFactory(nom="Mairie", slug="mairie")
    erp, sources, _ = mapper(service_public_valid, today=datetime(2021, 1, 1)).process()

    assert erp.published is True
    assert erp.user_id is None
    assert erp.source == ExternalSource.SOURCE_SERVICE_PUBLIC
    assert erp.source_id == "00007e4d-264c-43a0-b0b7-7f3b7dd995ab"
    assert erp.activite.slug == "mairie"
    assert erp.numero == "3"
    assert erp.voie == "Rue du général-roux"
    assert erp.code_postal == "77590"
    assert erp.commune == "Fontaine-le-Port"
    assert erp.code_insee == "77590"
    assert erp.geom.coords == (3.0, 43.0)
    assert erp.nom == "Mairie - Fontaine-le-Port"
    assert erp.telephone == "0164383052"
    assert erp.user_type == "system"

    assert erp.accessibilite.entree_plain_pied is False
    assert erp.accessibilite.entree_marches_rampe == "amovible"
    assert erp.accessibilite.entree_aide_humaine is True

    assert len(sources) == 1
    assert sources[0].source == ExternalSource.SOURCE_SERVICE_PUBLIC
    assert sources[0].source_id == "00007e4d-264c-43a0-b0b7-7f3b7dd995ab"

    assert erp.sources.count() == 1


@pytest.mark.usefixtures("service_public_valid")
def test_update_existing_erp(mapper, service_public_valid):  # noqa
    CommuneFactory(nom="Fontaine-le-Port")

    ActiviteFactory(nom="Mairie", slug="mairie")

    existing_erp = ErpFactory(
        source=ExternalSource.SOURCE_SERVICE_PUBLIC, source_id="00007e4d-264c-43a0-b0b7-7f3b7dd995ab"
    )
    AccessibiliteFactory(erp=existing_erp, entree_plain_pied=True, entree_aide_humaine=False)
    erp, sources, _ = mapper(service_public_valid, today=datetime(2021, 1, 1)).process()

    assert erp.pk == existing_erp.pk
    assert erp.accessibilite.entree_plain_pied is False
    assert erp.accessibilite.entree_marches_rampe == "amovible"
    assert erp.accessibilite.entree_aide_humaine is True

    assert len(sources) == 1
    assert sources[0].source == ExternalSource.SOURCE_SERVICE_PUBLIC
    assert sources[0].source_id == "00007e4d-264c-43a0-b0b7-7f3b7dd995ab"

    assert erp.sources.count() == 1
