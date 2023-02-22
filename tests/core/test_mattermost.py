from datetime import datetime

import pytest
import requests
from django.conf import settings

from core import mattermost


def test_send_simple(mocker):
    settings.MATTERMOST_HOOK = "http://fake"
    spy = mocker.spy(requests, "post")

    mattermost.send("foo", today=datetime(2021, 1, 1))

    spy.assert_called_once_with(
        "http://fake",
        json={"text": "localhost — 01/01/2021 à 00:00:00: foo\n#production"},
    )


def test_send_tags(mocker):
    settings.MATTERMOST_HOOK = "http://fake"
    spy = mocker.spy(requests, "post")

    mattermost.send("foo", tags=["abc", "def"], today=datetime(2021, 1, 1))

    spy.assert_called_once_with(
        "http://fake",
        json={"text": "localhost — 01/01/2021 à 00:00:00: foo\n#production #abc #def"},
    )
