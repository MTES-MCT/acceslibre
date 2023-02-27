import html

import pytest
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core import mail
from django.urls import reverse
from splinter import Browser

from erp import schema
from erp.models import Accessibilite, Activite, Commune, Erp


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


def test_home(data, browser):
    browser.visit(reverse("home"))

    assert browser.title.startswith("acceslibre")


def test_communes(data, browser):
    browser.visit(reverse("communes"))

    assert browser.title.startswith("Communes")
    assert len(browser.find_by_css("#home-communes-list .card")) == 1
    assert len(browser.find_by_css("#home-latest-erps-list a")) == 1


def test_erp_details(data, browser, erp_domtom):
    browser.visit(data.erp.get_absolute_url())

    assert "Aux bons croissants" in browser.title
    assert "Boulangerie" in browser.title
    assert "Jacou" in browser.title
    assert browser.is_text_present(data.erp.nom)
    assert browser.is_text_present(data.erp.activite.nom)
    assert browser.is_text_present(data.erp.adresse)
    assert browser.is_text_present(html.unescape(schema.get_help_text_ui("sanitaires_presence")))
    assert browser.is_text_present(html.unescape(schema.get_help_text_ui_neg("sanitaires_adaptes")))

    browser.visit(erp_domtom.get_absolute_url())

    assert "Lycée Joseph Zobel" in browser.title
    assert "Lycée" in browser.title
    assert "Rivière-Salée" in browser.title
    assert browser.is_text_present(erp_domtom.nom)
    assert browser.is_text_present(erp_domtom.activite.nom)
    assert browser.is_text_present(erp_domtom.adresse)
    assert browser.is_text_present(html.unescape(schema.get_help_text_ui("sanitaires_presence")))
    assert browser.is_text_present(html.unescape(schema.get_help_text_ui_neg("sanitaires_adaptes")))


def test_erp_details_edit_links(data, browser):
    browser.visit(data.erp.get_absolute_url())

    assert browser.title.startswith(data.erp.nom)
    edit_urls = [
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
    ]
    for edit_url in edit_urls:
        matches = browser.links.find_by_href(edit_url)
        assert len(matches) > 0, f'Edit url "{edit_url}" not found'


def test_registration_flow_without_next(data, browser):
    browser.visit(reverse("django_registration_register"))
    browser.fill("username", "johndoe")
    browser.fill("email", "john@doe.com")
    browser.fill("password1", "Abcdef123!")
    browser.fill("password2", "Abcdef123!")
    browser.check("robot")
    button = browser.find_by_css("form.registration-form button[type=submit]")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is False

    assert len(mail.outbox) == 1
    assert "Activation de votre compte" in mail.outbox[0].subject
    assert "johndoe" in mail.outbox[0].body
    assert "http://testserver/compte/activate" in mail.outbox[0].body

    activation_url = [
        line for line in mail.outbox[0].body.split("\n") if line.startswith("http") and "/activate/" in line
    ][0].strip()
    browser.visit(activation_url)

    assert browser.is_text_present("Votre compte est désormais actif")
    user = User.objects.get(username="johndoe")
    assert user.is_active is True


def test_registration_flow(data, browser):
    browser.visit(reverse("django_registration_register") + "?next=/contact/")
    browser.fill("username", "johndoe")
    browser.fill("email", "john@doe.com")
    browser.fill("password1", "Abcdef123!")
    browser.fill("password2", "Abcdef123!")
    browser.check("robot")
    button = browser.find_by_css("form.registration-form button[type=submit]")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is False

    assert len(mail.outbox) == 1
    assert "Activation de votre compte" in mail.outbox[0].subject
    assert "johndoe" in mail.outbox[0].body
    assert "http://testserver/compte/activate" in mail.outbox[0].body
    assert "?next=/contact/" in mail.outbox[0].body

    activation_url = [
        line for line in mail.outbox[0].body.split("\n") if line.startswith("http") and "/activate/" in line
    ][0].strip()
    browser.visit(activation_url)

    user = User.objects.get(username="johndoe")
    assert user.is_active is True

    # ensure we've been redirected to where we registered initially from
    assert browser.url == "/contact/"
    assert browser.is_text_present("Contactez-nous")
