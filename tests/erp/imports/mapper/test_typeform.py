import pytest
from django.core.management import call_command

from erp.management.commands.validate_and_import_file import Command
from erp.models import Activite, Erp
from tests.erp.imports.mapper.fixtures import vallorcine


@pytest.fixture
def activite_mairie(db):
    return Activite.objects.create(nom="Mairie")


def test_save_non_existing_erp(mocker, activite_mairie, vallorcine):
    mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)
    cm = Command()
    call_command(
        cm,
        file="data/tests/typeform_mairie_test_ok.csv",
        skip_import=False,
        mapper="typeform_mairie",
        send_emails=True,
    )

    assert cm.skip_import is False
    assert cm.results["in_error"]["count"] == 0
    assert cm.results["validated"]["count"] == 1
    assert cm.results["imported"]["count"] == 1

    erp = Erp.objects.last()

    assert erp.published is True
    assert erp.import_email == "secretaire.mairie@xxx.fr"
    assert erp.activite == activite_mairie
    assert erp.user_type == "system"
    assert erp.commune_ext == vallorcine
    assert erp.nom == "Mairie"

    mock_mail.assert_called_once_with(
        to_list="secretaire.mairie@xxx.fr",
        template="erp_imported",
        context={"erp_url": erp.get_absolute_uri()},
    )


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
    assert cm.results["validated"]["count"] == 0
    assert cm.results["imported"]["count"] == 0


def test_update_duplicate_erp(activite_mairie, vallorcine):
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
        force_update=True,
    )

    assert cm.results["duplicated"]["count"] == 1
    assert cm.results["validated"]["count"] == 1
    assert cm.results["imported"]["count"] == 1
