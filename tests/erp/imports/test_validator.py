import csv

import pytest
from django.core.management import call_command, CommandError

from erp.management.commands.validate_import_file import Command


def test_without_params_command():
    """
    File : {self.input_file}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    """
    with pytest.raises(CommandError):
        call_command("validate_import_file")


def test_skip_import_with_KO_file():
    """
    File : {self.input_file}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    """
    cm = Command()
    call_command(cm, file="data/generic_test_failed.csv", skip_import=True)

    assert cm.skip_import is True
    assert cm.results["in_error"]["count"] != 0
    assert cm.results["imported"]["count"] == 0


def test_one_line_with_KO_file():
    """
    File : {self.input_file}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    """
    cm = Command()
    call_command(cm, file="data/generic_test_failed.csv", one_line=True)

    assert cm.one_line is True
    assert cm.results["in_error"]["count"] == 1


def test_generate_error_file_with_KO_file():
    """
    File : {self.input_file}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    """
    cm = Command()
    call_command(cm, file="data/generic_test_failed.csv", generate_errors_file=True)

    assert cm.generate_errors_file is True
    assert cm.error_file is not None
    with open("errors.csv", "r") as error_file:
        reader = csv.DictReader(error_file, delimiter=";")
        assert len(list(reader)) == 5


def test_generate_error_file_with_KO_file_and_oneline():
    """
    File : {self.input_file}
    Verbose : {self.verbose}
    One Line : {self.one_line}
    Skip import : {self.skip_import}
    Generate Errors file : {self.generate_errors_file}
    """
    cm = Command()
    call_command(
        cm,
        file="data/generic_test_failed.csv",
        generate_errors_file=True,
        one_line=True,
    )

    assert cm.generate_errors_file is True
    assert cm.one_line is True
    assert cm.error_file is not None
    with open("errors.csv", "r") as error_file:
        reader = csv.DictReader(error_file, delimiter=";")
        assert len(list(reader)) == 1
