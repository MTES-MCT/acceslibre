import json
import pytest

from datetime import datetime

from django.contrib.gis.geos import Point

from erp.mapper.vaccination import RecordMapper
from erp.models import Activite, Erp

from tests.erp.mapper.fixtures import neufchateau, sample_record_ok


@pytest.fixture
def activite_cdv(db):
    return Activite.objects.create(nom="Centre de vaccination")


def test_init():
    with pytest.raises(RuntimeError) as err:
        RecordMapper({})
    assert "Propriété manquante 'geometry'" in str(err.value)

    with pytest.raises(RuntimeError) as err:
        RecordMapper({"geometry": []})
    assert "Propriété manquante 'properties'" in str(err.value)


def test_source_id():
    m = RecordMapper({"geometry": [], "properties": {"c_gid": 123}})
    assert m.source_id == "123"


def test_source_id_missing():
    with pytest.raises(RuntimeError) as err:
        m = RecordMapper({"geometry": [], "properties": {"c_gid": None}})
        m.source_id
    assert "Champ c_gid manquant" in str(err.value)


def test_skip_importing_closed(activite_cdv, neufchateau, sample_record_ok):
    sample_closed = sample_record_ok.copy()
    sample_closed["properties"]["c_date_fermeture"] = "2021-01-01"

    m = RecordMapper(sample_closed, today=datetime(2021, 1, 2))
    with pytest.raises(RuntimeError) as err:
        m.process(activite_cdv)

    assert "SKIPPED: Centre fermé le 2021-01-01" in str(err.value)


def test_skip_importing_reserve_pros(activite_cdv, neufchateau, sample_record_ok):
    sample_reserve_pros = sample_record_ok.copy()
    sample_reserve_pros["properties"][
        "c_rdv_modalites"
    ] = "Ouvert uniquement aux professionnels"

    m = RecordMapper(sample_reserve_pros)
    with pytest.raises(RuntimeError) as err:
        m.process(activite_cdv)

    assert (
        "SKIPPED: Réservé aux professionnels de santé: Ouvert uniquement aux professionnels"
        in str(err.value)
    )


def test_skip_importing_equipe_mobile(activite_cdv, neufchateau, sample_record_ok):
    sample_equipe_mobile = sample_record_ok.copy()
    sample_equipe_mobile["properties"]["c_rdv_modalites"] = "Equipe mobile"

    m = RecordMapper(sample_equipe_mobile)
    with pytest.raises(RuntimeError) as err:
        m.process(activite_cdv)

    assert "SKIPPED: Équipe mobile écartée: " in str(err.value)


def test_save_non_existing_erp(activite_cdv, neufchateau, sample_record_ok):
    m = RecordMapper(sample_record_ok, today=datetime(2021, 1, 1))

    erp = m.process(activite_cdv)

    assert erp.published is True
    assert erp.user_id is None
    assert erp.source == Erp.SOURCE_VACCINATION
    assert erp.source_id == "219"
    assert erp.activite == activite_cdv
    assert erp.numero == "1280"
    assert erp.voie == "Avenue de la Division Leclerc"
    assert erp.code_postal == "88300"
    assert erp.commune == "Neufchâteau"
    assert erp.commune_ext == neufchateau
    assert erp.code_insee == "88321"
    assert erp.geom.coords == (5.7076970492316, 48.370392643203)
    assert erp.nom == "Centre de vaccination de Neufchateau"
    assert erp.telephone == "+33329948605"
    assert erp.user_type == "system"
    assert erp.metadata == {
        "ban_addresse_id": "88321_0105_01281",
        "centre_vaccination": {
            "date_fermeture": None,
            "date_ouverture": "2021-01-08",
            "datemaj": "2021/02/04 16:21:11.620",
            "horaires_rdv": {
                "dimanche": "fermé",
                "jeudi": "14:00-18:00",
                "lundi": "14:00-18:00",
                "mardi": "14:00-18:00",
                "mercredi": "14:00-18:00",
                "samedi": "14:00-18:00",
                "vendredi": "14:00-18:00",
            },
            "modalites": None,
            "structure": {
                "nom": "AGENCE REGIONALE DE SANTE GRAND EST",
                "numero": "3",
                "voie": "BD JOFFRE",
                "code_postal": "54000",
                "commune": "NANCY",
                "code_insee": "54395",
            },
            "url_rdv": "https://partners.doctolib.fr/hopital-public/neufchateau/centre-de-vaccination-covid-neufchateau-et-vittel?speciality_id=5494&enable_cookies_consent=1",
        },
    }
    assert (
        "importées depuis data.gouv.fr le 01/01/2021" in erp.accessibilite.commentaire
    )


def test_update_existing_erp(activite_cdv, neufchateau, sample_record_ok):
    m1 = RecordMapper(sample_record_ok, today=datetime(2021, 1, 1))
    erp1 = m1.process(activite_cdv)

    # import updated data for the same Erp
    sample_record_ok_updated = sample_record_ok.copy()
    sample_record_ok_updated["properties"]["c_rdv_tel"] = "1234"
    m2 = RecordMapper(sample_record_ok_updated, today=datetime(2021, 1, 1))
    erp2 = m2.process(activite_cdv)

    assert erp1.id == erp2.id
    assert erp2.telephone == "1234"
    assert (
        "mises à jour depuis data.gouv.fr le 01/01/2021"
        in erp2.accessibilite.commentaire
    )


def test_unpublish_closed_erp(activite_cdv, neufchateau, sample_record_ok):
    m1 = RecordMapper(sample_record_ok, today=datetime(2021, 1, 1))
    m1.process(activite_cdv)

    # reimport the same record, but this time it's closed
    sample_closed = sample_record_ok.copy()
    sample_closed["properties"]["c_date_fermeture"] = "2021-01-01"
    m2 = RecordMapper(sample_closed, today=datetime(2021, 1, 2))

    with pytest.raises(RuntimeError) as err:
        m2.process(activite_cdv)
    assert "UNPUBLISHED" in str(err.value)
    assert (
        Erp.objects.find_by_source_id(Erp.SOURCE_VACCINATION, m2.source_id).published
        is False
    )
