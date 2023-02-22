import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError

from erp.imports.serializers import ErpImportSerializer
from erp.models import Erp
from tests.erp.imports.mapper.fixtures import jacou, paris


@pytest.mark.django_db
@pytest.mark.parametrize(
    "erp_values, is_valid, geocoder_result",
    (
        pytest.param({"siret": "Non renseigné"}, False, None, id="invalid_siret"),
        pytest.param({"siret": "48137888300021"}, True, None, id="valid_siret"),
        pytest.param({"nom": ""}, False, None, id="empty_name"),
        pytest.param({"code_postal": "99999"}, False, None, id="invalid_postal_code"),
        pytest.param({"code_postal": "348300"}, False, None, id="invalid_postal_code"),
        pytest.param({"activite": "Unknown in DB"}, False, None, id="invalid_activity"),
        pytest.param({"commune": "Unknown in DB"}, True, None, id="invalid_commune"),
        pytest.param(
            {
                "commune": "Unknown in DB",
                "numero": "125",
                "voie": "Rue des Pompiers",
                "code_postal": "86140",
            },
            False,
            {
                "geom": Point((0, 0)),
            },
            id="invalid_ban_adresse",
        ),
        pytest.param({"accessibilite": {}}, False, None, id="empty_accessibility"),
        pytest.param({"latitude": 0, "longitude": 0}, True, {"empty": True}, id="empty_geocoder"),
        pytest.param(
            {
                "activite": "Boulangerie",
                "numero": "4",
                "voie": "grand rue",
                "code_postal": "34830",
                "commune": "Jacou",
                "email": "importator@tierce.com",
            },
            False,
            {
                "geom": Point((0, 0)),
                "numero": "4",
                "voie": "grand rue",
                "code_postal": "34830",
                "commune": "Jacou",
                "code_insee": "34830",
            },
            id="duplicate",
        ),
    ),
)
def test_erp_import_serializer(mocker, data, erp_values, is_valid, geocoder_result, jacou, paris):
    mocker.patch(
        "erp.provider.geocoder.geocode",
        return_value=geocoder_result
        or {
            "geom": Point((0, 0)),
            "numero": "4",
            "voie": "Rue de la Paix",
            "lieu_dit": None,
            "code_postal": "75002",
            "commune": "Paris",
            "code_insee": "75111",
        },
    )

    initial_values = {
        "voie": "Rue de la Coquille",
        "code_postal": 34830,
        "commune": "Jacou",
        "nom": "Mairie",
        "activite": "Boulangerie",
        "accessibilite": {"entree_porte_presence": True},
        "latitude": 5,
        "longitude": 56,
    }
    serializer = ErpImportSerializer(data=initial_values | erp_values)

    assert serializer.is_valid() is is_valid, serializer.errors

    if is_valid:
        erp = serializer.save()
        assert isinstance(erp, Erp)
        assert erp.activite
        assert erp.accessibilite
        assert erp.geom.x == erp.geom.y == 0
        assert erp.import_email == erp_values.get("email")


def test_erp_update_serializer(data):
    assert data.erp.nom != "Aux bons pains"
    assert not data.accessibilite.entree_porte_presence

    serializer = ErpImportSerializer(
        instance=data.erp,
        data={"accessibilite": {"entree_porte_presence": True}, "nom": "Aux bons pains"},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    data.erp.refresh_from_db()
    assert data.erp.nom != "Aux bons pains", "Name should not be editable"
    assert data.accessibilite.entree_porte_presence is True
