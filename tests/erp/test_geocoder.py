import pytest
import requests

from erp import geocoder


def test_geocoder_error(mocker):
    mocker.patch(
        "requests.get", side_effect=requests.exceptions.RequestException("Boom"),
    )

    with pytest.raises(RuntimeError) as err:
        geocoder.geocode("xxx")
        assert "indisponible" in err
