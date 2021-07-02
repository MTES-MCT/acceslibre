import pytest

from django.core.management import call_command


def test_scheduler_setup(mocker):
    mocker.patch(  # skip actually running scheduled jobs indefinitely ;)
        "erp.management.commands.start_scheduler.Command.start"
    )

    call_command("start_scheduler")  # raises if improperly configurer
