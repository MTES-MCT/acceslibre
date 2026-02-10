from unittest import mock

import pytest
from django.core.management import call_command

from erp.models import Erp
from tests.factories import ErpFactory

csv_file_contents = """erp_id;"accueil_audiodescription_presence";"accueil_audiodescription";"entree_balise_sonore";"accueil_personnels";"commentaire"
18212;"False";;;;
158807;"True";"avec équipement permanent nécessitant le téléchargement d'une application sur smartphone";;;
145728;"True";"avec équipement permanent, casques et boîtiers disponibles à l’accueil";;;
165295;"True";"avec équipement permanent nécessitant le téléchargement d'une application sur smartphone";"False";;
"""


@pytest.mark.django_db
def test_nominal_case(mocker):
    erp1 = ErpFactory(nom="Pathé", pk=18212, with_accessibility=True)
    erp2 = ErpFactory(nom="CGR", pk=158807, with_accessibility=True)
    erp3 = ErpFactory(nom="Cinéma", pk=145728, with_accessibility=True)
    erp4 = ErpFactory(nom="Cinoche", pk=165295, with_accessibility=True)

    for erp in (erp1, erp2, erp3, erp4):
        erp.accessibilite.accueil_audiodescription_presence = True
        erp.accessibilite.accueil_audiodescription = [
            "avec équipement permanent nécessitant le téléchargement d'une application sur smartphone"
        ]
        erp.accessibilite.accueil_personnels = "aucun"
        erp.accessibilite.commentaire = "foo"
        erp.accessibilite.entree_balise_sonore = True
        erp.accessibilite.entree_porte_presence = True
        erp.accessibilite.save()

    with mock.patch("builtins.open", mock.mock_open(read_data=csv_file_contents)):
        call_command("import_aveugles", file="mocked_file")

    assert Erp.objects.count() == 4, "Should not create new ERP"

    for erp in (erp1, erp2, erp3, erp4):
        erp.refresh_from_db()
        erp.accessibilite.refresh_from_db()

        assert erp.accessibilite.entree_porte_presence is True
        assert erp.accessibilite.commentaire == "foo"

    assert erp1.accessibilite.accueil_audiodescription_presence is False
    assert not erp1.accessibilite.accueil_audiodescription

    assert erp2.accessibilite.accueil_audiodescription_presence is True
    assert erp2.accessibilite.accueil_audiodescription == ["avec_app"]

    assert erp3.accessibilite.accueil_audiodescription_presence is True
    assert erp3.accessibilite.accueil_audiodescription == ["avec_équipement_permanent"]

    assert erp4.accessibilite.accueil_audiodescription_presence is True
    assert erp4.accessibilite.accueil_audiodescription == ["avec_app"]
    assert erp4.accessibilite.entree_balise_sonore is False
