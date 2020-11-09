import pytest
import html

from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from splinter import Browser

from erp.models import Erp
from erp import schema

from tests.fixtures import data


@pytest.fixture
def browser():
    return Browser("django")


def login(browser, username, password, next=None):
    next_qs = f"?next={next}" if next else ""
    browser.visit(reverse("login") + next_qs)
    browser.fill("username", username)
    browser.fill("password", password)
    button = browser.find_by_css("form button[type=submit]")
    button.click()


def test_home(data, browser, capsys):
    browser.visit(reverse("home"))

    assert browser.title.startswith("Accueil")
    assert len(browser.find_by_css("#home-communes-list .card")) == 1

    assert data.erp.geom is not None
    assert data.erp.published is True
    assert data.erp.accessibilite is not None
    assert len(browser.find_by_css("#home-latest-erps-list a")) == 1


def test_erp_details(data, browser):
    browser.visit(data.erp.get_absolute_url())

    assert "Aux bons croissants" in browser.title
    assert "Boulangerie" in browser.title
    assert "Jacou" in browser.title
    assert browser.is_text_present(data.erp.nom)
    assert browser.is_text_present(data.erp.activite.nom)
    assert browser.is_text_present(data.erp.adresse)
    assert browser.is_text_present("Sanitaires")
    assert browser.is_text_present(
        html.unescape(schema.get_help_text_ui("sanitaires_presence"))
    )
    assert browser.is_text_present(
        html.unescape(schema.get_help_text_ui("sanitaires_adaptes"))
    )


def test_erp_details_edit_links(data, browser, capsys):
    browser.visit(data.erp.get_absolute_url())

    assert browser.title.startswith(data.erp.nom)
    edit_urls = [
        reverse("contrib_edit_infos", kwargs={"erp_slug": data.erp.slug}),
        reverse("contrib_sanitaires", kwargs={"erp_slug": data.erp.slug}),
    ]
    for edit_url in edit_urls:
        matches = browser.links.find_by_href(edit_url)
        assert len(matches) > 0, f'Edit url "{edit_url}" not found'


def test_registration_flow(data, browser):
    browser.visit(reverse("django_registration_register") + "?next=/contactez-nous/")
    browser.fill("username", "johndoe")
    browser.fill("first_name", "John")
    browser.fill("last_name", "Doe")
    browser.fill("email", "john@doe.com")
    browser.fill("password1", "Abcdef123!")
    browser.fill("password2", "Abcdef123!")
    button = browser.find_by_css("form button[type=submit]")
    button.click()

    user = User.objects.get(username="johndoe")
    assert user.is_active is False

    assert len(mail.outbox) == 1
    assert "Activation de votre compte" in mail.outbox[0].subject
    assert "johndoe" in mail.outbox[0].body
    assert "http://testserver/accounts/activate" in mail.outbox[0].body
    assert "?next=/contactez-nous/" in mail.outbox[0].body

    activation_url = [
        line
        for line in mail.outbox[0].body.split("\n")
        if line.startswith("http") and "/activate/" in line
    ][0].strip()
    browser.visit(activation_url)

    assert browser.is_text_present("Votre compte est désormais actif")
    user = User.objects.get(username="johndoe")
    assert user.is_active is True

    connect_link = browser.find_by_text("Je me connecte")
    connect_link.click()

    assert browser.is_text_present("Nom d’utilisateur")
    browser.fill("username", "johndoe")
    browser.fill("password", "Abcdef123!")
    button = browser.find_by_css("form button[type=submit]")
    button.click()

    # ensure we've been redirected to where we registered initially from
    assert browser.url == "/contactez-nous/"
    assert browser.is_text_present("Contactez-nous")
