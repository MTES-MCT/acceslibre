import random
from unittest import mock

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command

from erp.models import Erp
from tests.factories import ActiviteFactory, CommuneFactory

csv_file_contents = """"Libéllé de l'entité","Type de l'entité","Numéro et voie","Lieu-dit","Complément d'adresse","Code postal","Localité","Pays","ACH00002","ACH00014","ACH00015","ACH00009","ACH00003","ACH00010","ACH00011","ACH00004","ACH00007","ACH00001","ACH00008","ACH00012","ACH00005","ACH00006","ACH00013"
"AMBERIEU EN BUGEY","BUREAU CENTRE","38 RUE ALEXANDRE BERARD","BP 602",,"01500","AMBERIEU EN BUGEY","FRANCE","OUI","OUI","OUI","OUI","NC","OUI","OUI","OUI","OUI","OUI","OUI","OUI","OUI","OUI","OUI"
"AMBERIEU EN DOMBES BP","BUREAU DE POSTE","240 RUE GOMBETTE",,,"01330","AMBERIEUX EN DOMBES","FRANCE","NON","OUI","OUI","NC","NC","NON","OUI","OUI","NON","OUI","NON","NON","NC","NC","NON"
"CEYZERIAT","BUREAU CENTRE","RUE JEROME LALANDE"," "," ","01250","CEYZERIAT","FRANCE","OUI","OUI","OUI","NC","NC","NON","OUI","NC","OUI","OUI","OUI","OUI","OUI","OUI","OUI"
"""


@pytest.mark.django_db
def test_nominal_case(mocker):
    CommuneFactory(nom="AMBERIEU EN BUGEY")
    CommuneFactory(nom="AMBERIEUX EN DOMBES")
    CommuneFactory(nom="CEYZERIAT")
    ActiviteFactory(nom="Bureau de Poste")

    # random geo coords to avoid a matching by name.
    def _mock_geocode(*args, **kwargs):
        return {
            "geom": Point(random.randint(1, 90), random.randint(0, 180), srid=4326),
            "numero": random.randint(1, 9999),
            "voie": "Grand rue",
            "lieu_dit": None,
            "code_postal": kwargs["postcode"],
            "commune": "CEYZERIAT",
            "code_insee": kwargs["postcode"],
            "provider": "ban",
        }

    mocker.patch("erp.provider.geocoder.geocode", side_effect=_mock_geocode)

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_laposte", file="mocked_file")

    assert Erp.objects.count() == 3

    erp1 = Erp.objects.get(nom="La Poste", code_postal="01500")
    assert erp1.accessibilite.conformite is True
    assert erp1.accessibilite.entree_balise_sonore is True
    assert erp1.accessibilite.accueil_equipements_malentendants_presence is True
    assert erp1.accessibilite.accueil_equipements_malentendants == ["bim"]
    assert "Guichet avec tablette PMR" in erp1.accessibilite.commentaire
    assert "Présence d'un espace confidentiel accessible" in erp1.accessibilite.commentaire
    assert "Pick up accessible aux PMR" not in erp1.accessibilite.commentaire
    assert "GAB avec prise audio pour malvoyant" in erp1.accessibilite.commentaire

    erp2 = Erp.objects.get(nom="La Poste", code_postal="01330")
    assert erp2.accessibilite.conformite is False
    assert "Pas d'espace confidentiel accessible" in erp2.accessibilite.commentaire
