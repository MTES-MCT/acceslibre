import tempfile

import pytest
import requests
from django.test import Client
from django.urls import reverse

from tests.factories import ErpFactory, UserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def auth_client():
    admin = UserFactory(is_staff=True)
    client = Client()
    client.force_login(admin)
    return client


def format_error(m):
    message = m["message"]
    if "extract" in m:
        message = message + f"\n  Extract: {m['extract']}"
    return message


def validate_html(html):
    with tempfile.TemporaryFile() as fp:
        fp.write(str.encode(html))
        fp.seek(0)
        res = requests.post(
            "https://validator.w3.org/nu/",
            data=fp.read(),
            params={"out": "json"},
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36",
                "Content-Type": "text/html; charset=UTF-8",
            },
        )
    if res.status_code != 200:
        pytest.skip("Validator is unavailable.")
        return
    results = res.json()
    errors = [format_error(m) for m in results["messages"] if m["type"] == "error"]
    if errors:
        raise AssertionError("\n- ".join(["Errors encountered:"] + errors))


def validate_url_get(client, url):
    html = client.get(url).content.decode()
    validate_html(html)


@pytest.mark.django_db
def test_home(client):
    admin = UserFactory(is_staff=True)
    validate_url_get(client, reverse("home"))
    client.force_login(admin)
    validate_url_get(client, reverse("home"))


@pytest.mark.django_db
def test_home_auth(auth_client):
    validate_url_get(auth_client, reverse("home"))


@pytest.mark.django_db
def test_search_empty(client):
    validate_url_get(client, reverse("search"))


@pytest.mark.django_db
def test_search_result(client, mocker):
    validate_url_get(client, reverse("search") + "?where=jacou")


def fix_test_erp_details(client):
    erp = ErpFactory()
    validate_url_get(client, erp.get_absolute_url())


def fix_test_erp_details_auth(auth_client):
    erp = ErpFactory()
    validate_url_get(auth_client, erp.get_absolute_url())


def test_editorial_accessibilite(client):
    validate_url_get(client, reverse("accessibilite"))


def test_editorial_cgu(client):
    validate_url_get(client, reverse("cgu"))


def test_editorial_partenaires(client):
    validate_url_get(client, reverse("partenaires"))


@pytest.mark.django_db
def test_login(client):
    validate_url_get(client, reverse("login"))
