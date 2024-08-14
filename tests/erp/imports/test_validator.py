import csv
import os

import pytest
from django.core.management import CommandError, call_command
from django.test import override_settings
from reversion.models import Version
from sib_api_v3_sdk import AddContactToList

from erp.management.commands.validate_and_import_file import Command
from erp.models import Erp
from tests.erp.imports.mapper.fixtures import neufchateau  # noqa


class TestValidator:
    error_filename = "test_error.csv"

    def test_without_params_command(self):
        with pytest.raises(CommandError):
            call_command(Command())

    def test_skip_import_with_KO_file(self):
        cm = Command()
        call_command(cm, file="data/tests/generic_test_failed.csv", skip_import=True)

        assert cm.skip_import is True
        assert cm.results["in_error"]["count"] != 0
        assert cm.results["imported"]["count"] == 0

    def test_generate_error_file_with_KO_file(self, mocker):
        cm = Command()
        mocker.patch.object(cm, "_get_error_filename", return_value=self.error_filename)
        call_command(cm, file="data/tests/generic_test_failed.csv", generate_errors_file=True)

        assert cm.generate_errors_file is True
        assert cm.error_file is not None
        with open(cm.error_file_path, "r") as error_file:
            reader = csv.DictReader(error_file, delimiter=";")
            assert len(list(reader)) == 5

    @pytest.mark.usefixtures("activite")
    @pytest.mark.usefixtures("neufchateau")
    def test_skip_import_with_OK_file(self):
        cm = Command()
        call_command(cm, file="data/tests/generic_test_ok.csv", skip_import=True)

        assert cm.skip_import is True
        assert cm.results["in_error"]["count"] == 0
        assert cm.results["validated"]["count"] == 1

    @pytest.mark.usefixtures("activite")
    @pytest.mark.usefixtures("neufchateau")
    @override_settings(BREVO_CONTACT_LIST_IDS={"tally-respondents": 11})
    def test_with_OK_file(self, mocker):
        mock_brevo = mocker.patch("sib_api_v3_sdk.ContactsApi.add_contact_to_list", return_value=True)
        cm = Command()
        call_command(
            cm,
            file="data/tests/generic_test_ok.csv",
        )

        assert cm.skip_import is False
        assert cm.results["in_error"]["count"] == 0
        assert cm.results["validated"]["count"] == 1
        assert cm.results["imported"]["count"] == 1
        erp = Erp.objects.last()
        assert Version.objects.get_for_object(erp).count() == 1

        mock_brevo.assert_called_once_with(11, AddContactToList(emails=["test@gmail.com"]))

    @pytest.mark.usefixtures("activite")
    @pytest.mark.usefixtures("neufchateau")
    def test_duplicate_and_permanently_closed_with_OK_file(self):
        cm = Command()
        call_command(
            cm,
            file="data/tests/generic_test_ok.csv",
        )

        assert cm.results["in_error"]["count"] == 0
        assert cm.results["imported"]["count"] == 1
        assert cm.results["duplicated"]["count"] == 0
        assert cm.results["permanently_closed"]["count"] == 0

        call_command(
            cm,
            file="data/tests/generic_test_ok.csv",
        )

        assert cm.results["in_error"]["count"] == 0
        assert cm.results["imported"]["count"] == 0
        assert cm.results["duplicated"]["count"] == 1
        assert cm.results["permanently_closed"]["count"] == 0

        erp = Erp.objects.get(nom="400C Scotta!")
        erp.permanently_closed = True
        erp.save()

        call_command(
            cm,
            file="data/tests/generic_test_ok.csv",
        )

        assert cm.results["in_error"]["count"] == 0
        assert cm.results["imported"]["count"] == 0
        assert cm.results["duplicated"]["count"] == 0
        assert cm.results["permanently_closed"]["count"] == 1

    @pytest.mark.usefixtures("activite")
    @pytest.mark.usefixtures("neufchateau")
    def test_duplicate_with_OK_file_force(self):
        cm = Command()
        call_command(
            cm,
            file="data/tests/generic_test_ok.csv",
        )

        assert cm.results["in_error"]["count"] == 0
        assert cm.results["imported"]["count"] == 1
        assert cm.results["duplicated"]["count"] == 0

        call_command(cm, file="data/tests/generic_test_ok.csv", force_update=True)

        assert cm.results["in_error"]["count"] == 0
        assert cm.results["duplicated"]["count"] == 1
        assert cm.results["imported"]["count"] == 1
        assert cm.results["validated"]["count"] == 1

    def teardown_method(self, method):
        if os.path.exists(self.error_filename):
            os.remove(self.error_filename)
