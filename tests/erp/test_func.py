import re
from unittest.mock import ANY

import pytest
import responses
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils.translation import gettext as translate
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from splinter import Browser

from erp.models import Accessibilite, Activite, Commune, Erp
from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory


@pytest.fixture
def browser_chrome():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("prefs", {"intl.accept_languages": "fr_FR"})

    browser = Browser(driver_name="chrome", headless=True, options=options)
    browser.driver.set_window_size(1920, 1080)
    return browser


@pytest.fixture
def browser():
    return Browser("django")


@pytest.fixture
def erp_domtom():
    lycee, _ = Activite.objects.get_or_create(nom="Lycée")
    commune_ext, _ = Commune.objects.get_or_create(
        slug="972-riviere-salee",
        nom="Rivière-Salée",
        code_postaux=[97215],
        departement=972,
        geom=Point((-60.9737, 14.5327)),
    )
    erp = Erp.objects.create(
        nom="Lycée Joseph Zobel",
        numero="G27M+7J8",
        voie=" Quartier THORAILLE",
        code_postal="97215",
        commune="RIVIERE-SALEE",
        commune_ext=commune_ext,
        geom=Point((-60.968791544437416, 14.515293175686068)),
        activite=lycee,
        published=True,
        user=User.objects.first(),
    )
    Accessibilite.objects.create(erp=erp, sanitaires_presence=True, sanitaires_adaptes=False)
    return erp


def login(browser, username, password, next=None):
    next_qs = f"?next={next}" if next else ""
    browser.visit(reverse("login") + next_qs)
    browser.fill("username", username)
    browser.fill("password", password)
    button = browser.find_by_css("form button[type=submit]")
    button.click()


@pytest.mark.django_db
def test_home(browser, django_assert_max_num_queries):
    with django_assert_max_num_queries(3):
        browser.visit(reverse("home"))

    assert browser.title.startswith("acceslibre")


@pytest.mark.django_db
def test_communes(browser):
    CommuneFactory(nom="Jacou")
    ErpFactory()
    browser.visit(reverse("communes"))

    assert browser.title.startswith("Communes")
    assert len(browser.find_by_css("#home-communes-list .card")) == 1
    assert len(browser.find_by_css("#home-latest-erps-list a")) == 1


@pytest.mark.django_db
def test_erp_details(browser, erp_domtom, django_assert_max_num_queries):
    activite = ActiviteFactory(nom="Boulangerie")
    commune = CommuneFactory(nom="Jacou")
    erp = ErpFactory(
        nom="Aux bons croissants",
        activite=activite,
        commune="Jacou",
        commune_ext=commune,
        accessibilite__sanitaires_presence=True,
        accessibilite__sanitaires_adaptes=False,
        accessibilite__entree_porte_presence=True,
        accessibilite__entree_reperage=True,
    )
    with django_assert_max_num_queries(7):
        browser.visit(erp.get_absolute_url())

    assert "Aux bons croissants" in browser.title
    assert "Boulangerie" in browser.title
    assert "Jacou" in browser.title
    assert browser.is_text_present(erp.nom)
    assert browser.is_text_present(erp.activite.nom)
    assert browser.is_text_present(erp.adresse)
    assert browser.is_text_present(translate("Toilettes classiques"))
    assert browser.is_text_present(translate("Entrée bien visible"))

    with django_assert_max_num_queries(5):
        browser.visit(erp_domtom.get_absolute_url())

    assert "Lycée Joseph Zobel" in browser.title
    assert "Lycée" in browser.title
    assert "Rivière-Salée" in browser.title
    assert browser.is_text_present(erp_domtom.nom)
    assert browser.is_text_present(erp_domtom.activite.nom)
    assert browser.is_text_present(erp_domtom.adresse)


@pytest.mark.django_db
def test_erp_details_edit_links(browser):
    erp = ErpFactory(with_accessibilite=True)
    browser.visit(erp.get_absolute_url())

    assert browser.title.startswith(erp.nom)
    edit_urls = [
        reverse("contrib_edit_infos", kwargs={"erp_slug": erp.slug}),
    ]
    for edit_url in edit_urls:
        matches = browser.links.find_by_href(edit_url)
        assert len(matches) > 0, f'Edit url "{edit_url}" not found'


@pytest.mark.django_db
def test_registration_flow_without_next(mocker, browser):
    brevo_mock = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    browser.visit(reverse("django_registration_register"))
    browser.fill("username", "johndoe")
    browser.fill("email", "john@doe.com")
    browser.fill("password1", "Abc123456789!")
    browser.fill("password2", "Abc123456789!")
    browser.check("robot")
    button = browser.find_by_css("form.registration-form button[type=submit]")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is False

    assert brevo_mock.call_count == 1
    brevo_mock.assert_called_once_with(
        to_list="john@doe.com",
        template="account_activation",
        context={"activation_key": ANY, "username": "johndoe", "next": "/"},
    )

    key = brevo_mock.call_args_list[0][1]["context"]["activation_key"]
    activation_url = f"http://testserver/compte/activate/?activation_key={key}"
    browser.visit(activation_url)

    assert browser.is_text_present("Activer votre compte")
    button = browser.find_by_css("form#activation button")
    button.click()

    assert browser.is_text_present("Votre compte est désormais actif")
    user = User.objects.get(username="johndoe")
    assert user.is_active is True


@pytest.mark.django_db
def test_registration_flow(mocker, browser):
    brevo_mock = mocker.patch("core.mailer.BrevoMailer.send_email", return_value=True)

    browser.visit(reverse("django_registration_register") + "?next=/contact/")
    browser.fill("username", "johndoe")
    browser.fill("email", "john@doe.com")
    browser.fill("password1", "Abc123456789!")
    browser.fill("password2", "Abc123456789!")
    browser.check("robot")
    browser.check("newsletter_opt_in")
    button = browser.find_by_css("form.registration-form button[type=submit]")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is False

    assert brevo_mock.call_count == 1
    brevo_mock.assert_called_once_with(
        to_list="john@doe.com",
        template="account_activation",
        context={"activation_key": ANY, "username": "johndoe", "next": "/contact/"},
    )

    assert user.preferences.get().newsletter_opt_in is True

    key = brevo_mock.call_args_list[0][1]["context"]["activation_key"]
    activation_url = f"http://testserver/compte/activate/?activation_key={key}&next=/contact/"
    browser.visit(activation_url)

    assert browser.is_text_present("Activer votre compte")
    button = browser.find_by_css("form#activation button")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is True

    # ensure we've been redirected to where we registered initially from
    assert browser.url == "/contact/"
    assert browser.is_text_present("Contactez-nous")


@pytest.fixture
def mock_geo_api():
    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=re.compile(r"https://geo\.api\.gouv\.fr/communes.*"),
            json=[
                {
                    "nom": "Lyon",
                    "code": "69123",
                    "codesPostaux": ["69001", "69002"],
                    "codeDepartement": "69",
                    "centre": {"type": "Point", "coordinates": [4.8357, 45.764]},
                }
            ],
            status=200,
        )
        rsps.assert_all_requests_are_fired = False
        yield rsps


@pytest.mark.django_db
def test_contribution_anonymous(mocker, browser_chrome, mairie_jacou_result, akei_result, live_server, mock_geo_api):
    activity = ActiviteFactory(nom="Boulangerie Pâtisserie")
    ActiviteFactory(nom="Boucherie")
    erp = ErpFactory(
        commune="Lyon",
        numero=6,
        voie="rue de l'epargne",
        code_postal="69008",
        activite=activity,
        nom="La super boulang' de Solange",
        geom=Point(4.8352, 45.72),
    )
    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    browser_chrome.visit(live_server.url + reverse("contrib_start"))

    assert browser_chrome.is_text_present("Ajouter un établissement")

    browser_chrome.fill("what", "boulangerie")
    browser_chrome.fill("activite", "Bou")

    browser_chrome.driver.save_screenshot("screenshot.png")
    activities = WebDriverWait(browser_chrome.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".list-group#autocomplete-result-list-1 > li"))
    )

    assert activities
    boulangerie = browser_chrome.find_by_css(".list-group#autocomplete-result-list-1 > li").first
    assert boulangerie.text == "Boulangerie Pâtisserie"
    boulangerie.click()

    browser_chrome.fill("where", "Lyon")

    cities = WebDriverWait(browser_chrome.driver, 10).until(
        EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".autocomplete-result-list > li"), "Lyon (69)")
    )

    assert cities
    lyon = browser_chrome.find_by_css(".autocomplete-result-list > li").first
    assert lyon.text == "Lyon (69)"
    lyon.click()

    assert browser_chrome.find_by_name("where").value == "Lyon (69)"

    button = browser_chrome.find_by_css("form#search-form button[type=submit]").first

    WebDriverWait(browser_chrome.driver, 10).until(EC.element_to_be_clickable((button._element)))
    button.click()

    assert reverse("contrib_global_search") in browser_chrome.url
    assert "activity_slug=boulangerie-patisserie" in browser_chrome.url
    assert "where=Lyon" in browser_chrome.url
    assert "what=boulangerie" in browser_chrome.url
    assert "&lat=45.758&lon=4.8351" in browser_chrome.url

    h2s = browser_chrome.find_by_css("h2")
    assert h2s[0].html == "Étape 1 : vérifiez si l'établissement est déjà enregistré dans notre base"
    assert (
        h2s[1].html
        == '\n        Résultats trouvés pour \n        "\n        Lyon - \n        boulangerie - \n        Boulangerie Pâtisserie\n        "\n    '
    )
    assert h2s[2].html == "Autres établissements connus à ajouter et compléter"
    assert h2s[3].html == "Étape 2 : vous n’avez pas trouvé votre établissement ci-dessus"

    div_external_results = browser_chrome.find_by_id("external-results")
    assert "AKEI" in div_external_results.html

    div_internal_results = browser_chrome.find_by_id("internal-results")
    assert erp.nom in div_internal_results.html
