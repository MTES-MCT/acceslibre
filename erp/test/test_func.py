import pytest
import html

from django.urls import reverse
from splinter import Browser

from .fixtures import data
from erp.models import Erp
from erp import schema


@pytest.fixture
def browser():
    return Browser("django")


def test_home(data, browser, capsys):
    browser.visit(reverse("home"))

    assert browser.title == "Accueil | Access4all"
    assert len(browser.find_by_css("#home-communes-list .card")) == 1

    assert data.erp.geom is not None
    assert data.erp.published == True
    assert data.erp.accessibilite is not None
    assert len(browser.find_by_css("#home-latest-erps-list a")) == 1


def test_erp_details(data, browser):
    browser.visit(data.erp.get_absolute_url())

    assert browser.title == "Aux bons croissants | Boulangerie | Jacou | Access4all"
    assert browser.is_text_present(data.erp.nom)
    assert browser.is_text_present(data.erp.activite.nom)
    assert browser.is_text_present(data.erp.adresse)
    assert browser.is_text_present("Sanitaires")
    assert browser.is_text_present(
        html.unescape(schema.get_help_text("sanitaires_presence"))
    )
    assert browser.is_text_present(
        html.unescape(schema.get_help_text("sanitaires_adaptes"))
    )
