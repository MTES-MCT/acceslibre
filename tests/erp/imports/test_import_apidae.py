import json
import urllib.parse
from unittest.mock import MagicMock

import pytest
import requests
from django.contrib.gis.geos import Point

from erp.exceptions import PermanentlyClosedException
from erp.models import Activite, Commune, Erp, ExternalSource
from tests.factories import ActiviteFactory, ErpFactory


@pytest.fixture
def apidae_activites(db):
    """Activities required by import_apidae.Command.mapping_activities (class-level)."""
    for nom in (
        "Lieu de visite",
        "Hôtel",
        "Restaurant",
        "Commerce",
        "Chambre d'hôtes, gîte, pension, meublé de tourisme",
    ):
        Activite.objects.get_or_create(nom=nom)


@pytest.fixture(autouse=True)
def mock_celery_signals(mocker):
    mocker.patch("compte.signals.sync_user_attributes.delay")
    mocker.patch("erp.signals.compute_access_completion_rate.delay")
    mocker.patch("erp.signals.check_for_activity_suggestion_spam.delay")


@pytest.fixture
def command(apidae_activites):
    from erp.management.commands.import_apidae import Command

    cmd = Command()
    cmd.stdout = MagicMock()
    cmd.stderr = MagicMock()
    return cmd


class TestGetQueryForParams:
    def test_merges_auth_params_and_url_encodes(self, command):
        encoded = command._get_query_for_params({"count": 10, "first": 0})
        decoded = json.loads(urllib.parse.unquote(encoded))
        assert decoded["count"] == 10
        assert decoded["first"] == 0
        assert "projetId" in decoded
        assert "apiKey" in decoded


class TestDoRequest:
    def test_returns_json_on_success(self, command, mocker):
        mock_response = MagicMock()
        mock_response.json.return_value = {"foo": "bar"}
        mock_response.raise_for_status.return_value = None
        mocker.patch("requests.get", return_value=mock_response)

        assert command._do_request("http://example.com") == {"foo": "bar"}

    def test_returns_none_on_request_error(self, command, mocker):
        mocker.patch("requests.get", side_effect=requests.RequestException("boom"))
        assert command._do_request("http://example.com") is None

    def test_returns_none_on_http_error(self, command, mocker):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500")
        mocker.patch("requests.get", return_value=mock_response)
        assert command._do_request("http://example.com") is None

    def test_returns_none_on_non_json(self, command, mocker):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("not json")
        mock_response.text = "not json"
        mocker.patch("requests.get", return_value=mock_response)
        assert command._do_request("http://example.com") is None


class TestEnsureNotPermanentlyClosed:
    def test_raises_if_any_permanently_closed(self, command):
        e1 = MagicMock(permanently_closed=False)
        e2 = MagicMock(permanently_closed=True)
        with pytest.raises(PermanentlyClosedException):
            command._ensure_not_permanently_closed([e1, e2])

    def test_no_raise_when_none_closed(self, command):
        e1 = MagicMock(permanently_closed=False)
        e2 = MagicMock(permanently_closed=False)
        command._ensure_not_permanently_closed([e1, e2])

    def test_no_raise_for_empty(self, command):
        command._ensure_not_permanently_closed([])


class TestHasAccessInfo:
    def test_true_for_known_libelle(self, command):
        access_info = [{"libelleFr": "Entrée accessible"}]
        assert command._has_access_info(access_info) is True

    def test_false_for_unknown_libelle(self, command):
        access_info = [{"libelleFr": "Pas dans la liste"}]
        assert command._has_access_info(access_info) is False

    def test_false_for_empty(self, command):
        assert command._has_access_info([]) is False

    def test_true_among_others(self, command):
        access_info = [
            {"libelleFr": "Quelconque"},
            {"libelleFr": "Place réservée PMR"},
        ]
        assert command._has_access_info(access_info) is True


class TestGetMappedAccessInfo:
    def test_wheelchair_autonomy(self, command):
        info = [{"libelleFr": "Accessible en fauteuil roulant en autonomie"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["entree_largeur_mini"] == 80
        assert "Accessible en fauteuil roulant" in data["commentaire"]

    def test_pmr_reserved_parking(self, command):
        info = [{"libelleFr": "Place réservée PMR"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["stationnement_presence"] is True
        assert data["stationnement_pmr"] is True

    def test_pmr_adapted_parking(self, command):
        info = [{"libelleFr": "Place adaptée PMR"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["stationnement_presence"] is True
        assert "stationnement_pmr" not in data

    def test_hard_surface(self, command):
        info = [{"libelleFr": "Revêtement dur (goudron, ciment, plancher)"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["chemin_ext_presence"] is True
        assert data["cheminement_ext_terrain_stable"] is True

    def test_level_path(self, command):
        info = [{"libelleFr": "Cheminement de plain-pied"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["chemin_ext_presence"] is True
        assert data["chemin_ext_plain_pied"] is True

    def test_accessible_entry(self, command):
        info = [{"libelleFr": "Entrée accessible"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["entree_plain_pied"] is True
        assert data["entree_largeur_mini"] == 80

    def test_elevator_only_when_large(self, command):
        info = [{"libelleFr": "Ascenseur aux normes"}]
        assert command._get_mapped_access_info(info, False, False) == {}
        data = command._get_mapped_access_info(info, True, False)
        assert data["accueil_ascenseur_etage"] is True
        assert data["accueil_ascenseur_etage_pmr"] is True

    def test_shower_only_when_hosting(self, command):
        info = [{"libelleFr": "Douche avec assise + espace de circulation"}]
        assert command._get_mapped_access_info(info, False, False) == {}
        data = command._get_mapped_access_info(info, False, True)
        assert data["accueil_chambre_nombre_accessibles"] == 1
        assert data["accueil_chambre_douche_siege"] is True

    def test_wc_only_when_hosting(self, command):
        info = [{"libelleFr": "WC + barre d'appui + espace de circulation"}]
        assert command._get_mapped_access_info(info, False, False) == {}
        data = command._get_mapped_access_info(info, False, True)
        assert data["accueil_chambre_nombre_accessibles"] == 1
        assert data["accueil_chambre_sanitaires_barre_appui"] is True
        assert data["accueil_chambre_sanitaires_espace_usage"] is True

    def test_visual_alarm_only_when_hosting(self, command):
        info = [{"libelleFr": "Alarme visuelle avec flash lumineux"}]
        assert command._get_mapped_access_info(info, False, False) == {}
        data = command._get_mapped_access_info(info, False, True)
        assert data["accueil_chambre_equipement_alerte"] is True

    def test_magnetic_loop(self, command):
        info = [{"libelleFr": "Boucle magnétique disponible à l’accueil"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["accueil_equipements_malentendants_presence"] is True
        assert data["accueil_equipements_malentendants"] == ["bim"]

    def test_lsf(self, command):
        info = [{"libelleFr": "Possibilité de communiquer en Langue des Signes Française"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["accueil_equipements_malentendants_presence"] is True
        assert data["accueil_equipements_malentendants"] == ["lsf"]

    def test_no_inside_obstacles(self, command):
        info = [{"libelleFr": "Cheminement sans obstacles à l'intérieur"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["accueil_retrecissement"] is False

    def test_trained_staff(self, command):
        info = [{"libelleFr": "Personnel d’accueil sensibilisé à l’accueil des personnes en situation de handicap"}]
        data = command._get_mapped_access_info(info, False, False)
        assert data["accueil_personnels"] == "formés"

    def test_unknown_libelle_yields_empty(self, command):
        info = [{"libelleFr": "Inconnu"}]
        assert command._get_mapped_access_info(info, False, False) == {}

    def test_multiple_libelles_aggregate(self, command):
        info = [
            {"libelleFr": "Place réservée PMR"},
            {"libelleFr": "Entrée accessible"},
        ]
        data = command._get_mapped_access_info(info, False, False)
        assert data["stationnement_presence"] is True
        assert data["stationnement_pmr"] is True
        assert data["entree_plain_pied"] is True
        assert data["entree_largeur_mini"] == 80


class TestFindErpByNameAndCodePostal:
    @pytest.mark.django_db
    def test_returns_published_erp(self, command):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        activite = ActiviteFactory(nom="Musée")
        erp = ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=activite,
            published=True,
            geom=Point(0, 0),
            user=None,
        )
        found = command._find_erp_by_name_and_code_postal("Musée des Arts", "69001")
        assert found == erp

    @pytest.mark.django_db
    def test_returns_none_when_no_match(self, command):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        activite = ActiviteFactory(nom="Musée")
        ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=activite,
            published=True,
            geom=Point(0, 0),
            user=None,
        )
        assert command._find_erp_by_name_and_code_postal("Musée des Arts", "75001") is None

    @pytest.mark.django_db
    def test_raises_when_permanently_closed(self, command):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        activite = ActiviteFactory(nom="Musée")
        ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=activite,
            published=True,
            permanently_closed=True,
            geom=Point(0, 0),
            user=None,
        )
        with pytest.raises(PermanentlyClosedException):
            command._find_erp_by_name_and_code_postal("Musée des Arts", "69001")


class TestParsePage:
    def _list_response(self, ids, num_found=None):
        return {"objetTouristiqueIds": ids, "numFound": num_found if num_found is not None else len(ids)}

    def _detail(
        self,
        oid,
        name="Musée des Arts",
        code_postal="69001",
        commune="Lyon",
        adresse1="1 rue X",
        typ="PATRIMOINE_CULTUREL",
        access=None,
    ):
        return {
            "id": oid,
            "type": typ,
            "nom": {"libelleFr": name},
            "localisation": {
                "adresse": {
                    "codePostal": code_postal,
                    "commune": {"nom": commune},
                    "adresse1": adresse1,
                }
            },
            "prestations": {"tourismesAdaptes": access or []},
        }

    @pytest.mark.django_db
    def test_no_touristic_objects_stops(self, command, mocker):
        mocker.patch.object(command, "_do_request", return_value={"objetTouristiqueIds": [], "numFound": 0})
        command._parse_page(0)
        # Single call only (list endpoint).
        assert command._do_request.call_count == 1

    @pytest.mark.django_db
    def test_skips_when_no_access_info_field(self, command, mocker):
        list_resp = self._list_response([1])
        detail = self._detail(1, access=[])
        # No "tourismesAdaptes" -> walrus returns falsy; should not crash.
        detail["prestations"]["tourismesAdaptes"] = None
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])
        command._parse_page(0)
        assert Erp.objects.count() == 0

    @pytest.mark.django_db
    def test_skips_when_no_mapped_access_libelle(self, command, mocker):
        list_resp = self._list_response([1])
        detail = self._detail(1, access=[{"libelleFr": "Inconnu"}])
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])
        command._parse_page(0)
        assert Erp.objects.count() == 0

    @pytest.mark.django_db
    def test_skips_unmapped_activity_type(self, command, mocker):
        list_resp = self._list_response([1])
        detail = self._detail(
            1,
            typ="EQUIPEMENT",
            access=[{"libelleFr": "Entrée accessible"}],
        )
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])
        command._parse_page(0)
        assert Erp.objects.count() == 0

    @pytest.mark.django_db
    def test_skips_permanently_closed(self, command, mocker):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        activite = ActiviteFactory(nom="Musée")
        ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=activite,
            published=True,
            permanently_closed=True,
            geom=Point(0, 0),
            user=None,
        )
        list_resp = self._list_response([1])
        detail = self._detail(1, access=[{"libelleFr": "Entrée accessible"}])
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])
        command._parse_page(0)
        # Should not create new ERP nor blow up.
        assert Erp.objects.count() == 1
        assert not ExternalSource.objects.filter(source=ExternalSource.SOURCE_APIDAE).exists()

    @pytest.mark.django_db
    def test_creates_new_erp_when_not_found(self, command, mocker, activite):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        list_resp = self._list_response([42])
        detail = self._detail(
            42,
            name="Nouveau Musée",
            access=[
                {"libelleFr": "Entrée accessible"},
                {"libelleFr": "Place réservée PMR"},
            ],
        )
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])

        command._parse_page(0)

        erp = Erp.objects.get(nom="Nouveau Musée")
        assert erp.code_postal == "69001"
        assert erp.accessibilite.stationnement_presence is True
        assert erp.accessibilite.stationnement_pmr is True
        assert erp.accessibilite.entree_plain_pied is True
        assert ExternalSource.objects.filter(erp=erp, source=ExternalSource.SOURCE_APIDAE, source_id="42").exists()

    @pytest.mark.django_db
    def test_updates_existing_erp(self, command, mocker, activite):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        existing = ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=Activite.objects.get(nom="Lieu de visite"),
            published=True,
            geom=Point(0, 0),
            user=None,
            with_accessibility=True,
        )
        existing.refresh_from_db()
        list_resp = self._list_response([7])
        detail = self._detail(7, name="Musée des Arts", access=[{"libelleFr": "Place réservée PMR"}])
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])

        command._parse_page(0)

        existing.refresh_from_db()
        existing.accessibilite.refresh_from_db()
        assert existing.accessibilite.stationnement_presence is True
        assert existing.accessibilite.stationnement_pmr is True

    @pytest.mark.django_db
    def test_recurses_to_next_page_when_more_results(self, command, mocker, activite):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        # First page: full count signals more pages; second page: empty.
        page0 = {"objetTouristiqueIds": [1], "numFound": 200}
        page1 = {"objetTouristiqueIds": [], "numFound": 0}
        detail = self._detail(1, access=[{"libelleFr": "Inconnu"}])
        mocker.patch.object(command, "_do_request", side_effect=[page0, detail, page1])

        command._parse_page(0)

        # 2 list calls + 1 detail
        assert command._do_request.call_count == 3

    @pytest.mark.django_db
    def test_enrich_only_when_existing_has_user(self, command, mocker, activite):
        Commune.objects.create(nom="Lyon", slug="lyon", departement="69", geom=Point(0, 0))
        existing = ErpFactory(
            nom="Musée des Arts",
            commune="Lyon",
            code_postal="69001",
            activite=Activite.objects.get(nom="Lieu de visite"),
            published=True,
            geom=Point(0, 0),
            with_accessibility=True,
        )
        assert existing.user is not None

        list_resp = self._list_response([99])
        detail = self._detail(99, name="Musée des Arts", access=[{"libelleFr": "Place réservée PMR"}])
        mocker.patch.object(command, "_do_request", side_effect=[list_resp, detail])

        serializer_mock = MagicMock()
        serializer_mock.is_valid.return_value = True
        serializer_mock.save.return_value = existing
        ser_cls = mocker.patch(
            "erp.management.commands.import_apidae.ErpImportSerializer",
            return_value=serializer_mock,
        )

        command._parse_page(0)

        _, kwargs = ser_cls.call_args
        assert kwargs["context"] == {"enrich_only": True}


@pytest.mark.django_db
def test_handle_starts_at_page_0(command, mocker):
    parse = mocker.patch.object(command, "_parse_page")
    command.handle()
    parse.assert_called_once_with(0)


@pytest.mark.django_db
def test_mapping_activities_resolves_known_keys(command):
    # Module-level mapping resolves DB names; unmapped types are None.
    from erp.management.commands.import_apidae import Command

    assert Command.mapping_activities["EQUIPEMENT"] is None
    assert Command.mapping_activities["FETE_ET_MANIFESTATION"] is None
    assert Command.mapping_activities["PATRIMOINE_CULTUREL"].nom == "Lieu de visite"
    assert Command.mapping_activities["HOTELLERIE"].nom == "Hôtel"
    assert Command.mapping_activities["RESTAURATION"].nom == "Restaurant"
    assert Command.mapping_activities["COMMERCE_ET_SERVICE"].nom == "Commerce"
