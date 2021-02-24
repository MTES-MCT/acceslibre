import json
import pytest

from datetime import datetime

from django.contrib.gis.geos import Point

from erp.mapper.vaccination import RecordMapper
from erp.models import Activite, Erp

from tests.erp.mapper.fixtures import (
    neufchateau,
    sample_record_ok,
    sample_record_reserve_ps,
)


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


def test_build_metadata(sample_record_reserve_ps):
    m = RecordMapper(sample_record_reserve_ps)

    assert m.build_metadata() == {
        "ban_addresse_id": "30334_0270_00016_bis",
        "centre_vaccination": {
            "date_fermeture": "2021-02-01",
            "date_ouverture": "2021-01-13",
            "datemaj": "2021/02/04 12:07:14.218",
            "horaires_rdv": {
                "dimanche": "fermé",
                "jeudi": "fermé",
                "lundi": "fermé",
                "mardi": "fermé",
                "mercredi": "9:00-16:30",
                "samedi": "fermé",
                "vendredi": "9:00-16:30",
            },
            "modalites": "Réservé aux professionnels de santé",
            "structure": {
                "code_insee": "34172",
                "code_postal": "34000",
                "commune": "MONTPELLIER",
                "nom": "AGENCE REGIONALE DE SANTE OCCITANIE",
                "numero": "1025",
                "voie": "AV HENRI BECQUEREL",
            },
            "url_rdv": "https://partners.doctolib.fr/hopital-public/uzes/centre-de-vaccination-covid-ch-le-mas-careiron?pid=practice-164184&enable_cookies_consent=1",
        },
    }


def test_build_commentaire(sample_record_reserve_ps):
    m = RecordMapper(sample_record_reserve_ps, today=datetime(2021, 1, 1))

    assert "importées depuis data.gouv.fr le 01/01/2021" in m.build_commentaire()


def test_check_closed():
    # closed vaccination center
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {"c_date_fermeture": "2021-01-01"},
        },
        today=datetime(2021, 1, 2),
    )
    assert m.check_closed() == datetime(2021, 1, 1)

    # active vaccination center
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {"c_date_fermeture": "2021-01-03"},
        },
        today=datetime(2021, 1, 2),
    )
    assert m.check_closed() is None


def test_check_reserve_ps():
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {
                "c_rdv_modalites": "R\u00e9serv\u00e9 aux professionnels de sant\u00e9",
            },
        }
    )
    assert m.check_reserve_ps() == "R\u00e9serv\u00e9 aux professionnels de sant\u00e9"


def test_check_equipe_mobile():
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {"c_rdv_modalites": "Equipe mobile"},
        }
    )
    assert m.check_equipe_mobile() == "Equipe mobile"


def test_extract_coordinates():
    m = RecordMapper(
        {
            "geometry": {
                "type": "MultiPoint",
                "coordinates": [[4.4130655367765, 44.008294265819]],
            },
            "properties": {},
        }
    )
    assert m.extract_coordinates() == Point(4.4130655367765, 44.008294265819)


def test_fetch_or_create_erp_non_existing(activite_cdv):
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {"c_gid": "test_new"},
        }
    )

    m.fetch_or_create_erp(activite_cdv)

    assert m.erp is not None
    assert m.erp_exists is False
    assert m.erp.source_id == "test_new"


def test_fetch_or_create_erp_existing(activite_cdv):
    existing_erp = Erp.objects.create(
        nom="plop",
        source=Erp.SOURCE_VACCINATION,
        source_id="test_existing",
    )
    m = RecordMapper(
        {
            "geometry": [],
            "properties": {"c_gid": "test_existing"},
        }
    )

    m.fetch_or_create_erp(activite_cdv)

    assert m.erp is not None
    assert m.erp_exists is True
    assert m.erp.id == existing_erp.id
    assert m.erp.source_id == "test_existing"


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

    # let's import updated data for the same Erp
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
