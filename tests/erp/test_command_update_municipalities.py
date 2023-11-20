from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from core.lib import geo
from erp.models import Commune
from tests.factories import CommuneFactory

LIST_JSON = [
    {
        "nom": "L'Abergement-Clémenciat",
        "code": "01001",
        "codeDepartement": "01",
        "siren": "210100012",
        "codeEpci": "200069193",
        "codeRegion": "84",
        "codesPostaux": ["01400"],
        "population": 806,
    }
]
DETAILS_JSON = {
    "nom": "L'Abergement-Clémenciat",
    "code": "01001",
    "codeDepartement": "01",
    "codesPostaux": ["01400"],
    "population": 806,
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
@patch("erp.management.commands.update_municipalities.requests.get")
def test_command_will_create_unknown_commune(mocked_requests):
    mocked_list = MagicMock()
    mocked_list.json.return_value = LIST_JSON
    mocked_details = MagicMock()
    mocked_details.json.return_value = DETAILS_JSON
    mocked_requests.side_effect = [mocked_list, mocked_details]

    assert Commune.objects.count() == 0
    call_command("update_municipalities", write=True)

    assert Commune.objects.count() == 1
    commune = Commune.objects.get()

    assert commune.nom == "L'Abergement-Clémenciat"
    assert commune.code_insee == "01001"
    assert commune.departement == "01"
    assert commune.code_postaux == ["01400"]
    assert commune.population == 806
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
@patch("erp.management.commands.update_municipalities.requests.get")
def test_command_will_update_commune(mocked_requests):
    CommuneFactory(
        nom="Outdated commune",
        code_insee="01001",
        departement="02",
        population=10,
        code_postaux=["01401"],
        contour=geo.geojson_mpoly(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0.0, 0.0],
                        [4.957825, 46.153507],
                        [4.958097, 46.153422],
                        [4.958412, 46.153273],
                        [0.0, 0.0],
                    ]
                ],
            }
        ),
    )

    mocked_list = MagicMock()
    mocked_list.json.return_value = LIST_JSON
    mocked_details = MagicMock()
    mocked_details.json.return_value = DETAILS_JSON
    mocked_requests.side_effect = [mocked_list, mocked_details]

    call_command("update_municipalities", write=True)

    commune = Commune.objects.get()

    assert commune.nom == "L'Abergement-Clémenciat"
    assert commune.code_insee == "01001"
    assert commune.departement == "01"
    assert commune.code_postaux == ["01400"]
    assert commune.population == 806
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
@patch("erp.management.commands.update_municipalities.requests.get")
def test_make_obsolete_old_commune_without_erp(mocked_requests):
    commune = CommuneFactory(obsolete=False)
    mocked_list = MagicMock(return_value=[])
    mocked_requests.side_effect = [mocked_list]

    call_command("update_municipalities", write=True)

    commune.refresh_from_db()
    assert commune.obsolete is True
