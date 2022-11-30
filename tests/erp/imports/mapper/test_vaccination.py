from datetime import datetime

import pytest

from erp.imports.mapper import SkippedRecord
from erp.imports.mapper.vaccination import (
    RAISON_EN_ATTENTE,
    RAISON_EQUIPE_MOBILE,
    RAISON_PUBLIC_RESTREINT,
    RAISON_RESERVE_CARCERAL,
    RAISON_RESERVE_PS,
    VaccinationMapper,
)
from erp.models import Activite, Erp
from tests.erp.imports.mapper.fixtures import neufchateau, sample_record_ok


@pytest.fixture
def activite_cdv(db):
    return Activite.objects.create(nom="Centre de vaccination")


@pytest.fixture
def mapper(db, activite_cdv):
    def _factory(record, today=None):
        return VaccinationMapper(record, activite_cdv, today=today)

    return _factory


def test_init(mapper):
    with pytest.raises(RuntimeError) as err:
        mapper({}).process()

    assert "Propriété manquante 'geometry'" in str(err.value)

    with pytest.raises(RuntimeError) as err:
        mapper({"geometry": []}).process()

    assert "Propriété manquante 'properties'" in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [
        {"c_rdv_site_web": "Doctolib"},
        {"c_rdv_site_web": None},
    ],
)
def test_handle_malformed_rdv_url(mapper, updates, neufchateau, sample_record_ok):
    sample_malformed_rdv_url = sample_record_ok.copy()
    sample_malformed_rdv_url["properties"].update(updates)

    erp, _ = mapper(sample_malformed_rdv_url).process()

    assert erp.metadata["centre_vaccination"]["url_rdv"] is None


def test_source_id(mapper, neufchateau, sample_record_ok):
    erp, _ = mapper(sample_record_ok.copy()).process()

    assert erp.source_id == "219"


def test_source_id_missing(mapper):
    with pytest.raises(RuntimeError) as err:
        m, _ = mapper({"geometry": [], "properties": {"c_gid": None}}).process()
        m.source_id

    assert "Champ c_gid manquant" in str(err.value)


def test_skip_importing_closed(mapper, neufchateau, sample_record_ok):
    sample_closed = sample_record_ok.copy()
    sample_closed["properties"]["c_date_fermeture"] = "2021-01-01"

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_closed, today=datetime(2021, 1, 2)).process()

    assert "Centre fermé le 2021-01-01" in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [
        {
            "c_reserve_professionels_sante": True,
        },
        {
            "c_nom": "XXX réservé aux professionnels de santé",
            "c_rdv_modalites": None,
        },
        {
            "c_nom": "XXX",
            "c_rdv_modalites": "réservé aux professionnels de santé",
        },
        {
            "c_nom": "XXX réservé PS",
            "c_rdv_modalites": None,
        },
    ],
)
def test_skip_importing_reserve_pros(mapper, updates, neufchateau, sample_record_ok):
    sample_reserve_pros = sample_record_ok.copy()
    sample_reserve_pros["properties"].update(updates)

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_reserve_pros).process()

    assert RAISON_RESERVE_PS in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [{"c_centre_fermeture": True}],
)
def test_skip_importing_reserve_public_restreint(
    mapper, updates, neufchateau, sample_record_ok
):
    sample_public_restreint = sample_record_ok.copy()
    sample_public_restreint["properties"].update(updates)

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_public_restreint).process()

    assert RAISON_PUBLIC_RESTREINT in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [
        {"c_nom": "XXX Equipe mobile", "c_rdv_modalites": None},
        {"c_nom": "XXX équipe mobile", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "Équipe mobile"},
        {"c_nom": "XXX", "c_rdv_modalites": "equipe mobile"},
    ],
)
def test_skip_importing_equipe_mobile(mapper, updates, neufchateau, sample_record_ok):
    sample_equipe_mobile = sample_record_ok.copy()
    sample_equipe_mobile["properties"].update(updates)

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_equipe_mobile).process()

    assert RAISON_EQUIPE_MOBILE in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [
        {"c_nom": "XXX en attente", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "en attente"},
    ],
)
def test_skip_importing_en_attente(mapper, updates, neufchateau, sample_record_ok):
    sample_en_attente = sample_record_ok.copy()
    sample_en_attente["properties"].update(updates)

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_en_attente).process()

    assert RAISON_EN_ATTENTE in str(err.value)


@pytest.mark.parametrize(
    "updates",
    [
        {"c_nom": "Centre pénitentiaire", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "Établissement Pénitentiaire"},
        {"c_nom": "Centre de détention", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "centre de détention"},
        {"c_nom": "Prison des Baumettes", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "réservé prison"},
        {"c_nom": "UHSA Baumettes", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "réservé UHSA"},
        {"c_nom": "UHSI Baumettes", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "réservé UHSI"},
        {"c_nom": "USMP Baumettes", "c_rdv_modalites": None},
        {"c_nom": "XXX", "c_rdv_modalites": "réservé USMP"},
    ],
)
def test_skip_importing_etablissements_penitentiares(
    mapper, updates, neufchateau, sample_record_ok
):
    sample_en_attente = sample_record_ok.copy()
    sample_en_attente["properties"].update(updates)

    with pytest.raises(SkippedRecord) as err:
        mapper(sample_en_attente).process()

    assert RAISON_RESERVE_CARCERAL in str(err.value)


def test_save_non_existing_erp(mapper, neufchateau, sample_record_ok, activite_cdv):
    erp, _ = mapper(sample_record_ok, today=datetime(2021, 1, 1)).process()

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
            "acces_sur_rdv": True,
            "prevaccination": True,
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


def test_update_existing_erp(mapper, neufchateau, sample_record_ok):
    m1 = mapper(sample_record_ok, today=datetime(2021, 1, 1))
    erp1, _ = m1.process()
    erp1.accessibilite.commentaire = "user contrib"
    erp1.save()
    erp1.accessibilite.save()

    # import updated data for the same Erp
    sample_record_ok_updated = sample_record_ok.copy()
    sample_record_ok_updated["properties"]["c_rdv_tel"] = "1234"
    m2 = mapper(sample_record_ok_updated, today=datetime(2021, 1, 2))
    erp2, _ = m2.process()

    assert erp1.id == erp2.id
    assert erp2.telephone == "1234"
    assert "user contrib" in erp2.accessibilite.commentaire
