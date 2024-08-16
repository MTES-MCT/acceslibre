from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from erp.models import Commune
from tests.factories import CommuneFactory, ErpFactory

LIST_JSON = [
    {
        "nom": "L'Abergement-Clémenciat",
        "code": "01001",
        "departement": "01",
        "codesPostaux": ["01400"],
        "population": 806,
        "type": "commune-actuelle",
    }
]
DETAILS_JSON = {
    "centre": {"type": "Point", "coordinates": [2.1191, 48.8039]},
}


@pytest.fixture(scope="function", autouse=True)
def mock_file(mocker):
    mocker.patch("erp.management.commands.update_municipalities.Command._get_file", return_value=MagicMock())
    mocker.patch("builtins.open", return_value=MagicMock())


@pytest.mark.django_db
@patch("erp.management.commands.update_municipalities.Command._get_details")
@patch("erp.management.commands.update_municipalities.json.load")
def test_command_will_create_unknown_commune(mocked_file, mocked_details):
    mocked_file.return_value = LIST_JSON

    mocked_details.return_value = DETAILS_JSON

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


@pytest.mark.django_db
@patch("erp.management.commands.update_municipalities.json.load")
def test_command_will_update_commune(mocked_file):
    commune = CommuneFactory(
        nom="Outdated commune",
        code_insee="01001",
        departement="02",
        population=10,
        code_postaux=["01401"],
    )
    assert commune.slug == "02-outdated-commune"

    mocked_file.return_value = LIST_JSON
    call_command("update_municipalities", write=True)

    commune = Commune.objects.get()

    assert commune.nom == "L'Abergement-Clémenciat"
    assert commune.code_insee == "01001"
    assert commune.departement == "01"
    assert commune.code_postaux == ["01400"]
    assert commune.population == 806
    assert commune.slug == "01-labergement-clemenciat"


@pytest.mark.django_db
@patch("erp.management.commands.update_municipalities.json.load")
def test_make_obsolete_old_commune_without_erp(mocked_file):
    commune = CommuneFactory(obsolete=False, code_insee="01001")
    data = deepcopy(LIST_JSON)
    data[0]["type"] = "commune-deleguee"
    mocked_file.return_value = data

    call_command("update_municipalities", write=True)

    commune.refresh_from_db()
    assert commune.obsolete is True


@pytest.mark.django_db
@patch("erp.management.commands.update_municipalities.json.load")
def test_make_obsolete_old_commune_with_erp(mocked_file):
    commune = CommuneFactory(obsolete=False, code_insee="01001")
    new_commune = CommuneFactory(obsolete=False, code_insee="05005")
    erp = ErpFactory(commune_ext=commune)

    data = deepcopy(LIST_JSON)
    data[0]["type"] = "commune-deleguee"
    data[0]["chefLieu"] = "05005"
    mocked_file.return_value = data

    call_command("update_municipalities", write=True)

    commune.refresh_from_db()
    erp.refresh_from_db()
    assert commune.obsolete is True
    assert erp.commune_ext == new_commune
