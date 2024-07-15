from unittest.mock import ANY

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils.translation import gettext as translate
from splinter import Browser

from erp.models import Accessibilite, Activite, Commune, Erp
from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory


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
    activation_url = f"http://testserver/compte/activate/{key}"
    browser.visit(activation_url)

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
    activation_url = f"http://testserver/compte/activate/{key}?next=/contact/"
    browser.visit(activation_url)

    user = User.objects.get(username="johndoe")
    assert user.is_active is True

    # ensure we've been redirected to where we registered initially from
    assert browser.url == "/contact/"
    assert browser.is_text_present("Contactez-nous")
