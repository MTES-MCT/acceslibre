from unittest.mock import patch

import pytest
from django.core.management import call_command

from erp.models import Commune
from tests.factories import CommuneFactory

DETAILS_JSON = {
    "centre": {"type": "Point", "coordinates": [2.1191, 48.8039]},
    "contour": {
        "type": "Polygon",
        "coordinates": [
            [
                [4.956045, 46.153859],
                [4.957825, 46.153507],
                [4.958097, 46.153422],
                [4.958412, 46.153273],
                [4.956045, 46.153859],
            ]
        ],
    },
}


@pytest.mark.django_db
@patch("erp.management.commands.update_geometry.requests.get")
def test_command_will_update_geom(mocked_api):
    commune = CommuneFactory(code_insee="01001")
    assert commune.contour is None
    mocked_api.return_value.json.return_value = DETAILS_JSON

    call_command("update_geometry", write=True)
    mocked_api.assert_called_once_with("https://geo.api.gouv.fr/communes/01001?fields=contour,centre")

    commune = Commune.objects.get()
    assert commune.geom.coords == (2.1191, 48.8039)
    assert commune.contour.coords[0] == (
        (
            (4.956045, 46.153859),
            (4.957825, 46.153507),
            (4.958097, 46.153422),
            (4.958412, 46.153273),
            (4.956045, 46.153859),
        ),
    )


@pytest.mark.django_db
@patch("erp.management.commands.update_geometry.requests.get")
def test_command_not_update_obsolete_object(mocked_api):
    commune = CommuneFactory(code_insee="01001", obsolete=True)
    assert commune.contour is None

    call_command("update_geometry", write=True)
    mocked_api.assert_not_called()
