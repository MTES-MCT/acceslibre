from datetime import datetime

import pytest

from erp.imports.mapper.service_public import ServicePublicMapper
from erp.models import Erp
from tests.erp.imports.mapper.fixtures import service_public_valid  # noqa
from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory


@pytest.fixture
def mapper(db):
    def _factory(record, today=None):
        return ServicePublicMapper(record, today=today)

    return _factory


def test_init(mapper):
    assert mapper({}).process() == (None, None)


def test_save_non_existing_erp(mapper, service_public_valid):  # noqa
    CommuneFactory(nom="Fontaine-le-Port")
    ActiviteFactory(nom="Mairie", slug="mairie")
    erp, _ = mapper(service_public_valid, today=datetime(2021, 1, 1)).process()

    assert erp.published is True
    assert erp.user_id is None
    assert erp.source == Erp.SOURCE_SERVICE_PUBLIC
    assert erp.source_id == "mairie-77188-01"
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


@pytest.mark.usefixtures("service_public_valid")
def test_update_existing_erp(mapper, service_public_valid):  # noqa
    CommuneFactory(nom="Fontaine-le-Port")

    ActiviteFactory(nom="Mairie", slug="mairie")

    existing_erp = ErpFactory(source=Erp.SOURCE_SERVICE_PUBLIC, source_id="mairie-77188-01")
    AccessibiliteFactory(erp=existing_erp, entree_plain_pied=True, entree_aide_humaine=False)
    erp, _ = mapper(service_public_valid, today=datetime(2021, 1, 1)).process()

    assert erp.pk == existing_erp.pk

    assert erp.accessibilite.entree_plain_pied is False
    assert erp.accessibilite.entree_marches_rampe == "amovible"
    assert erp.accessibilite.entree_aide_humaine is True
