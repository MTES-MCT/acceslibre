import time
from unittest.mock import ANY

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils.translation import gettext as translate
from selenium.webdriver.chrome.options import Options
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

    browser = Browser(driver_name="chrome", headless=True, options=options)
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


@pytest.mark.django_db
def test_contribution_anonymous(mocker, browser_chrome, mairie_jacou_result, akei_result, live_server):
    activity = ActiviteFactory(nom="Boulangerie Pâtisserie")
    erp = ErpFactory(commune="Lyon", activite=activity, nom="La super boulang' de Solange")
    mocker.patch(
        "erp.provider.search.global_search",
        return_value=[mairie_jacou_result, akei_result],
    )

    browser_chrome.visit(live_server.url + reverse("contrib_start"))

    assert browser_chrome.is_text_present("Ajouter un établissement")

    browser_chrome.fill("what", "boulangerie")
    browser_chrome.fill("activite", "Boulangerie Pâtisserie")
    browser_chrome.fill("where", "Lyon")

    assert browser_chrome.find_by_css(".autocomplete-result-list > li")
    time.sleep(2)  # FIXME to remove after mock ?
    lyon = browser_chrome.find_by_css(".autocomplete-result-list > li").first
    assert lyon.text == "Lyon (69)"
    lyon.click()

    time.sleep(1)

    button = browser_chrome.find_by_css("form#search-form button[type=submit]").first
    button.click()

    assert reverse("contrib_global_search") in browser_chrome.url
    assert "activite=Boulangerie+P%C3%A2tisserie" in browser_chrome.url
    assert "where=Lyon" in browser_chrome.url
    assert "what=boulangerie" in browser_chrome.url

    h2s = browser_chrome.find_by_css("h2")
    assert h2s[0].html == "Étape 1 : vérifiez si l'établissement est déjà enregistré dans notre base"
    assert (
        h2s[1].html
        == '\n        Résultats trouvés pour \n        "\n        Lyon - \n        boulangerie - \n        Boulangerie Pâtisserie\n        "\n    '
    )
    assert h2s[2].html == "Autres établissements connus à ajouter et compléter"
    assert h2s[3].html == "Étape 2 : vous n’avez pas trouvé votre établissement ci-dessus"

    # </div> containing internal DB results
    div_internal_results = browser_chrome.find_by_css("#internal-results-count-container").first
    assert erp.nom in div_internal_results
    ...

    # </div> containing external results
    div_external_results = browser_chrome.find_by_xpath("(//h2)[3]/following-sibling::div[1]").first
    assert "1 résultat" in div_external_results.html
    ...
