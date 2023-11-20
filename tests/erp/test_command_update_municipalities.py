from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from erp.models import Commune


@pytest.mark.django_db
@patch("erp.management.commands.update_municipalities.requests.get")
def test_command_will_create_unknown_commune(mocked_requests):
    mocked_list = MagicMock()
    mocked_list.json.return_value = [
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
    mocked_details = MagicMock()
    mocked_details.json.return_value = {
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
