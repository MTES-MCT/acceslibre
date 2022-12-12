import pytest

from django.core.management import call_command

from erp.management.commands.validate_import_file import Command

from erp.models import Activite, Erp
from tests.erp.imports.mapper.fixtures import vallorcine


@pytest.fixture
def activite_mairie(db):
    return Activite.objects.create(nom="Mairie")


def test_save_non_existing_erp(activite_mairie, vallorcine):
    cm = Command()
    call_command(
        cm,
        file="data/tests/typeform_mairie_test_ok.csv",
        skip_import=False,
        mapper="typeform_mairie",
    )

    assert cm.skip_import is False
    assert cm.results["in_error"]["count"] == 0
    assert cm.results["validated"]["count"] == 1
    assert cm.results["imported"]["count"] == 1

    erp = Erp.objects.last()

    assert erp.published is True
    assert erp.import_email == "secretaire.mairie@vallorcine.fr"
    assert erp.activite == activite_mairie
    assert erp.user_type == "system"


def test_nosave_duplicate_erp(activite_mairie, vallorcine):
    cm = Command()
    call_command(
        cm,
        file="data/tests/typeform_mairie_test_ok.csv",
        skip_import=False,
        mapper="typeform_mairie",
    )

    assert cm.skip_import is False
    assert cm.results["in_error"]["count"] == 0
    assert cm.results["validated"]["count"] == 1
    assert cm.results["imported"]["count"] == 1
    assert cm.results["duplicated"]["count"] == 0

    call_command(
        cm,
        file="data/tests/typeform_mairie_test_ok.csv",
        skip_import=False,
        mapper="typeform_mairie",
    )

    assert cm.results["duplicated"]["count"] == 1
