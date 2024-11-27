import copy
import uuid
from datetime import timedelta
from io import StringIO
from unittest.mock import ANY

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from erp.management.commands.convert_tally_to_schema import Command as CommandConvertTallyToSchema
from erp.management.commands.notify_daily_draft import Command as CommandNotifyDailyDraft
from erp.management.commands.outscraper_clean_closed import IGNORED_ACTIVITIES
from erp.models import Erp, ExternalSource
from tests.factories import AccessibiliteFactory, ActiviteFactory, CommuneFactory, ErpFactory


class TestConvertTallyToSchema:
    def test_process_line(self):
        line = {
            "Est-ce qu’il y a au moins une place handicapé dans votre parking ?": "Oui, nous avons une place handicapé",
            "cp": "4100",
            "adresse": "7 grande rue, Saint Martin en Haut",
            "Combien de marches y a-t-il pour entrer dans votre établissement ?": "124",
            "email": "contrib@beta.gouv.fr",
            "Si oui, liste des équipements d'aide à l'audition et à la communication ? (Boucle à induction magnétique portative)": "true",
            "Si oui, liste des équipements d'aide à l'audition et à la communication ? (Boucle à induction magnétique fixe)": "true",
        }
        expected_line = {
            "stationnement_presence": True,
            "stationnement_pmr": True,
            "code_postal": "04100",
            "code_insee": "04100",
            "lieu_dit": None,
            "numero": "7",
            "voie": "Grande rue",
            "commune": "Saint Martin en Haut",
            "entree_marches": 124,
            "import_email": "contrib@beta.gouv.fr",
            "source": "tally",
            "accueil_equipements_malentendants": ANY,  # checked above as it is not ordered
        }
        result = CommandConvertTallyToSchema()._process_line(line)
        assert result == expected_line
        result["accueil_equipements_malentendants"].sort()
        assert result["accueil_equipements_malentendants"] == ["bim", "bmp"]


class TestNotifyDraft:
    @override_settings(REAL_USER_NOTIFICATION=True)
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "creation_date, published, should_send_email",
        (
            pytest.param(
                timezone.now() - timedelta(days=1, hours=2),
                False,
                False,
                id="too_old",
            ),
            pytest.param(
                timezone.now() - timedelta(minutes=55),
                False,
                False,
                id="too_recent",
            ),
            pytest.param(
                timezone.now() - timedelta(days=1),
                False,
                True,
                id="already_published",
            ),
            pytest.param(
                timezone.now() - timedelta(days=1),
                True,
                False,
                id="ok",
            ),
        ),
    )
    def test_handle(self, mocker, creation_date, published, should_send_email):
        mock_mail = mocker.patch("core.mailer.BrevoMailer.send_email")
        erp = ErpFactory(published=published)
        erp.created_at = creation_date  # cannot be set on factory params, as it is a auto_now_add attr
        erp.save()

        CommandNotifyDailyDraft().handle()

        assert mock_mail.call_count == int(should_send_email)

        if should_send_email:
            mock_mail.assert_called_once_with(
                to_list=erp.user.email,
                template="draft",
                context={"publish_url": f"/contrib/publication/{erp.slug}/"},
            )


@pytest.mark.django_db
def test_remove_duplicates_with_same_accessibility_data():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    duplicate = main_erp
    duplicate.pk = None
    duplicate.uuid = uuid.uuid4()
    duplicate.nom = "Mairie - Lyon"
    duplicate.save()

    duplicate_access = main_erp.accessibilite
    duplicate_access.pk = None
    duplicate_access.erp = duplicate
    duplicate_access.save()

    assert Erp.objects.count() == 2

    call_command("remove_duplicate_mairie", write=True)

    assert Erp.objects.count() == 1


@pytest.mark.django_db
def test_remove_duplicates_with_same_accessibility_data_keeps_aspid():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    duplicate = main_erp
    duplicate.pk = None
    duplicate.uuid = uuid.uuid4()
    duplicate.nom = "Mairie - Lyon"
    duplicate.asp_id = "123"
    duplicate.save()

    duplicate_access = main_erp.accessibilite
    duplicate_access.pk = None
    duplicate_access.erp = duplicate
    duplicate_access.save()

    assert Erp.objects.count() == 2

    call_command("remove_duplicate_mairie", write=True)

    assert Erp.objects.count() == 1
    assert Erp.objects.get().asp_id == "123"


@pytest.mark.django_db
def test_merge_and_remove_duplicates_with_different_accessibility_data():
    main_erp = AccessibiliteFactory(stationnement_presence=None, erp__nom="Mairie de Lyon").erp

    duplicate = main_erp
    duplicate.pk = None
    duplicate.uuid = uuid.uuid4()
    duplicate.nom = "Mairie - Lyon"
    duplicate.asp_id = "123"
    duplicate.save()

    duplicate_access = main_erp.accessibilite
    duplicate_access.pk = None
    duplicate_access.erp = duplicate
    duplicate_access.stationnement_presence = True
    duplicate_access.save()

    assert Erp.objects.count() == 2

    call_command("remove_duplicate_mairie", write=True)

    assert Erp.objects.count() == 1
    assert Erp.objects.get().accessibilite.stationnement_presence is True
    assert Erp.objects.get().asp_id == "123"


@pytest.mark.django_db
def test_leave_untouched_multiple_duplicates():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    for _ in range(0, 3):
        duplicate = main_erp
        duplicate.pk = None
        duplicate.source = ExternalSource.SOURCE_PUBLIC
        duplicate.uuid = uuid.uuid4()
        duplicate.nom = "Mairie - Lyon"
        duplicate.save()

        duplicate_access = main_erp.accessibilite
        duplicate_access.pk = None
        duplicate_access.erp = duplicate
        duplicate_access.stationnement_presence = True
        duplicate_access.save()

    assert Erp.objects.count() == 4

    out = StringIO()
    call_command("remove_duplicate_mairie", write=True, stderr=out)
    assert Erp.objects.count() == 4
    # Every ERP will be checked for duplicates, printing 4 messages
    assert (
        out.getvalue()
        == """3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case
3 ERPs found - Need to improve merge strategy in this case\n"""
    )


@pytest.mark.django_db
def test_leave_untouched_multiple_different_asp_ids():
    main_erp = AccessibiliteFactory(erp__nom="Mairie de Lyon").erp

    for i in range(0, 3):
        duplicate = main_erp
        duplicate.pk = None
        duplicate.uuid = uuid.uuid4()
        duplicate.nom = "Mairie - Lyon"
        duplicate.asp_id = f"ASP {i}"
        duplicate.save()

        duplicate_access = main_erp.accessibilite
        duplicate_access.pk = None
        duplicate_access.erp = duplicate
        duplicate_access.save()

    assert Erp.objects.count() == 4

    out = StringIO()
    call_command("remove_duplicate_mairie", write=True, stderr=out)

    assert Erp.objects.count() == 4
    assert out.getvalue().startswith("Can't find the correct ASP ID") is True


class TestOutscraperAcquisition:
    initial_outscraper_response = [
        [
            {
                "query": "restaurant, Lyon",
                "name": "Le Troisième Art - Restaurant Gastronomique Lyon",
                "place_id": "ChIJzZhX5juz9UcR74W_abcd",
                "google_id": "0x47f5b33be65798cd:0x8ac44e3b5cbfabcd",
                "full_address": "173 Rue des tournesols, 69006 Lyon, France",
                "street": "173 Rue des tournesols",
                "postal_code": "69006",
                "country_code": "FR",
                "country": "France",
                "city": "Lyon",
                "latitude": 45.767984399999996,
                "longitude": 4.8563522,
                "site": "https://www.troisiemeart.fr",
                "phone": "+33 4 72 14 12 14",
                "type": "Restaurant",
                "description": "Restaurant chic",
                "category": "restaurants",
                "subtypes": "Restaurant, Restaurant français, Restaurant gastronomique",
                "cid": "9999203089535436271",
                "business_status": "OPERATIONAL",
                "about": {
                    "Accessibilité": {
                        "Entrée accessible en fauteuil roulant": True,
                        "Toilettes accessibles en fauteuil roulant": True,
                        "Parking accessible en fauteuil roulant": True,
                    },
                },
            }
        ]
    ]

    @pytest.mark.django_db
    def test_initial(self, mocker):
        ActiviteFactory(nom="Restaurant")
        CommuneFactory(nom="Lyon")
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=self.initial_outscraper_response)
        call_command("outscraper_acquisition", query="Lyon", activity="Restaurant")

        erp = Erp.objects.get(nom="Le Troisième Art - Restaurant Gastronomique Lyon")
        assert erp.source == ExternalSource.SOURCE_OUTSCRAPER
        assert erp.source_id == "ChIJzZhX5juz9UcR74W_abcd"
        assert erp.site_internet == "https://www.troisiemeart.fr"
        assert erp.numero == "173"
        assert erp.voie == "Rue des tournesols"
        assert erp.code_postal == "69006"
        assert erp.commune == "Lyon"
        assert erp.accessibilite.entree_plain_pied is True
        assert erp.accessibilite.sanitaires_presence is True
        assert erp.accessibilite.sanitaires_adaptes is True
        assert erp.accessibilite.stationnement_ext_presence is True
        assert erp.accessibilite.stationnement_ext_pmr is True

        # call the command twice, it should not create a second erp
        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant")

        assert (
            Erp.objects.filter(nom="Le Troisième Art - Restaurant Gastronomique Lyon").count() == 1
        ), "should not create a second ERP"

    @pytest.mark.django_db
    def test_deletion(self, mocker):
        mock_response = copy.deepcopy(self.initial_outscraper_response)
        mock_response[0][0]["business_status"] = "CLOSED_PERMANENTLY"

        activite = ActiviteFactory(nom="Restaurant")
        CommuneFactory(nom="Lyon")
        AccessibiliteFactory(
            entree_plain_pied=False,
            erp__nom="Le Troisième Art - Restaurant Gastronomique Lyon",
            erp__commune="Lyon",
            erp__numero=173,
            erp__voie="Rue des tournesols",
            erp__activite=activite,
        ).erp
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=mock_response)

        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant")

        assert (
            Erp.objects.filter(nom="Le Troisième Art - Restaurant Gastronomique Lyon").count() == 0
        ), "should have deleted the closed_permanently ERP"

    @pytest.mark.django_db
    def test_update(self, mocker):
        activite = ActiviteFactory(nom="Restaurant")

        existing_erp = AccessibiliteFactory(
            entree_plain_pied=None,
            erp__nom="Le Troisième Art - Restaurant Gastronomique Lyon",
            erp__commune="Lyon",
            erp__numero=173,
            erp__voie="Rue des tournesols",
            erp__activite=activite,
            erp__source="gendarmerie",
            erp__source_id="abc",
        ).erp
        CommuneFactory(nom="Lyon")
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=self.initial_outscraper_response)
        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant")

        existing_erp.refresh_from_db()

        assert existing_erp.accessibilite.entree_plain_pied is True, "should have updated access info"

        existing_erp.accessibilite.entree_plain_pied = False
        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant")

        existing_erp.refresh_from_db()

        assert existing_erp.accessibilite.entree_plain_pied is True, "should not alter existing access info"

        assert existing_erp.sources.count() == 2

    @pytest.mark.django_db
    def test_not_enough_info(self, mocker):
        outscraper_response = [
            [
                {
                    "query": "restaurant, Lyon",
                    "name": "Le Troisième Art - Restaurant Gastronomique Lyon",
                    "place_id": "ChIJzZhX5juz9UcR74W_abcd",
                    "google_id": "0x47f5b33be65798cd:0x8ac44e3b5cbfabcd",
                    "full_address": "173 Rue des tournesols, 69006 Lyon, France",
                    "street": "173 Rue des tournesols",
                    "postal_code": "69006",
                    "country_code": "FR",
                    "country": "France",
                    "city": "Lyon",
                    "latitude": 45.767984399999996,
                    "longitude": 4.8563522,
                    "site": "https://www.troisiemeart.fr",
                    "phone": "+33 4 72 14 12 14",
                    "type": "Restaurant",
                    "description": "Restaurant chic",
                    "category": "restaurants",
                    "subtypes": "Restaurant, Restaurant français, Restaurant gastronomique",
                    "cid": "9999203089535436271",
                    "business_status": "OPERATIONAL",
                    "about": {
                        "Accessibilité": {},
                    },
                }
            ]
        ]

        ActiviteFactory(nom="Restaurant")
        CommuneFactory(nom="Lyon")
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=outscraper_response)
        call_command("outscraper_acquisition", query="Lyon", activity="Restaurant")

        assert not Erp.objects.filter(nom="Le Troisième Art - Restaurant Gastronomique Lyon")

    @pytest.mark.django_db
    def test_max_results(self, mocker):
        mock = mocker.patch("outscraper.ApiClient.google_maps_search", return_value=self.initial_outscraper_response)

        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant", max_results=1)
        assert mock.call_count == 1

        mock.reset_mock()
        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant", max_results=2)
        assert mock.call_count == 1

        mock.reset_mock()
        mock = mocker.patch(
            "outscraper.ApiClient.google_maps_search", return_value=[self.initial_outscraper_response[0] * 20]
        )
        call_command("outscraper_acquisition", query="restaurant, Lyon", activity="Restaurant", max_results=30)
        assert mock.call_count == 2


class TestOutscraperCleaning:
    initial_outscraper_response = [
        [
            {
                "query": "restaurant, Lyon",
                "name": "Le lard",
                "place_id": "ChIJzZhX5juz9UcR74W_abcd",
                "google_id": "0x47f5b33be65798cd:0x8ac44e3b5cbf85ef",
                "full_address": "140 Rue Trouvier, 69006 Lyon, France",
                "street": "173 Rue Trouvier",
                "postal_code": "69006",
                "country_code": "FR",
                "country": "France",
                "city": "Lyon",
                "latitude": 45.767984399999996,
                "longitude": 4.8563522,
                "site": "https://www.lelard.com/?utm_source=google+",
                "phone": "+33 4 72 14 12 14",
                "type": "Restaurant",
                "description": "Restaurant gras.",
                "category": "restaurants",
                "subtypes": "Restaurant, Restaurant français, Restaurant grastronomique",
                "cid": "9999203089535436271",
                "business_status": "CLOSED_PERMANENTLY",
                "about": {
                    "Accessibilité": {
                        "Entrée accessible en fauteuil roulant": True,
                        "Toilettes accessibles en fauteuil roulant": True,
                    },
                },
            }
        ]
    ]

    def setup_method(self, method):
        for name in IGNORED_ACTIVITIES:
            ActiviteFactory(nom=name)

    @pytest.mark.django_db
    def test_initial(self, mocker):
        ErpFactory(nom="Le lard", commune="Lyon", voie="Rue Trouvier", numero=173, activite__nom="Restaurant")
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=self.initial_outscraper_response)

        call_command("outscraper_clean_closed", nb_days=0, write=False)
        assert (
            Erp.objects.filter(nom="Le lard", published=True, permanently_closed=False).count() == 1
        ), "should not have flag it, no write param"

        call_command("outscraper_clean_closed", nb_days=0, write=True)
        assert Erp.objects.filter(nom="Le lard", published=True).count() == 0, "should have flagged & unpublished it"

    @pytest.mark.django_db
    def test_no_response(self, mocker):
        erp = ErpFactory(nom="no match")
        mocker.patch("outscraper.ApiClient.google_maps_search", return_value=[{}])

        call_command("outscraper_clean_closed", nb_days=0, write=True)

        erp.refresh_from_db()
        assert erp.check_closed_at is not None, "should have set a check_closed_at date"

    @pytest.mark.django_db
    def test_to_ignore(self, mocker):
        erp = ErpFactory(nom="Le lard", commune="Lyon", voie="Rue Trouvier", numero=173, activite__nom="Mairie")
        google_maps_mock = mocker.patch("outscraper.ApiClient.google_maps_search", return_value=[{}])

        call_command("outscraper_clean_closed", nb_days=0, write=True)

        assert not google_maps_mock.called
        erp.refresh_from_db()
        assert erp.check_closed_at is None


class TestScrapflyAcquisition:
    initial_scrapfly_list_response = [
        {
            "name": "Le Troisième Art - Restaurant Gastronomique Lyon",
            "url": "https://boorking.com/3e-art",
        }
    ]

    initial_scrapfly_detail_response = {
        "id": "ChIJzZhX5juz9UcR74W_abcd",
        "title": "Le Troisième Art - Restaurant Gastronomique Lyon",
        "address": "173 Rue des tournesols, Lyon",
        "features": {
            "Accessibilité": ["Toilettes avec barres d'appui", "Accessible en fauteuil roulant"],
            "Parking": ["Parking accessible aux personnes à mobilité réduite"],
        },
    }

    @pytest.mark.django_db
    def test_initial(self, mocker):
        ActiviteFactory(nom="Hôtel")
        CommuneFactory(nom="Lyon", code_postaux=[69006])
        mocker.patch("scrapfly.ScrapflyClient.scrape")
        mocker.patch(
            "erp.management.commands.scrapfly_acquisition.Command._search",
            return_value=self.initial_scrapfly_list_response,
        )
        mocker.patch(
            "erp.management.commands.scrapfly_acquisition.Command._parse_hotel",
            return_value=self.initial_scrapfly_detail_response,
        )
        call_command("scrapfly_acquisition", query="Lyon")

        erp = Erp.objects.get(nom="Le Troisième Art - Restaurant Gastronomique Lyon")
        assert erp.source == ExternalSource.SOURCE_SCRAPFLY
        assert erp.source_id == "ChIJzZhX5juz9UcR74W_abcd"
        assert erp.site_internet is None
        assert erp.numero == "173"
        assert erp.voie == "Rue des tournesols"
        assert erp.code_postal == "34830"
        assert erp.commune == "Lyon"
        assert erp.accessibilite.entree_plain_pied is True
        assert erp.accessibilite.entree_largeur_mini == 80
        assert erp.accessibilite.accueil_chambre_sanitaires_barre_appui is True
        assert erp.accessibilite.stationnement_presence is True
        assert erp.accessibilite.stationnement_pmr is True

        # call the command twice, it should not create a second erp
        call_command("scrapfly_acquisition", query="restaurant, Lyon")

        assert (
            Erp.objects.filter(nom="Le Troisième Art - Restaurant Gastronomique Lyon").count() == 1
        ), "should not create a second ERP"

    @pytest.mark.django_db
    def test_update(self, mocker):
        activite = ActiviteFactory(nom="Hôtel")

        existing_erp = AccessibiliteFactory(
            entree_plain_pied=None,
            erp__nom="Le Troisième Art - Restaurant Gastronomique Lyon",
            erp__commune="Lyon",
            erp__numero=173,
            erp__voie="Rue des tournesols",
            erp__activite=activite,
        ).erp
        CommuneFactory(nom="Lyon")
        mocker.patch("scrapfly.ScrapflyClient.scrape")
        mocker.patch(
            "erp.management.commands.scrapfly_acquisition.Command._search",
            return_value=self.initial_scrapfly_list_response,
        )
        mocker.patch(
            "erp.management.commands.scrapfly_acquisition.Command._parse_hotel",
            return_value=self.initial_scrapfly_detail_response,
        )
        call_command("scrapfly_acquisition", query="Lyon")

        existing_erp.refresh_from_db()

        assert existing_erp.accessibilite.entree_plain_pied is True, "should have updated access info"

        existing_erp.accessibilite.entree_plain_pied = False
        call_command("scrapfly_acquisition", query="Lyon")

        existing_erp.refresh_from_db()

        assert existing_erp.accessibilite.entree_plain_pied is True, "should not alter existing access info"
