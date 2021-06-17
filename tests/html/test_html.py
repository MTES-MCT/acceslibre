import pytest
import requests
import tempfile

from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def auth_client(data):
    client = Client()
    client.force_login(data.admin)
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
    if len(errors) > 0:
        raise AssertionError("\n- ".join(["Errors encountered:"] + errors))


def validate_url_get(client, url):
    html = client.get(url).content.decode()
    validate_html(html)


def test_home(data, client):
    validate_url_get(client, reverse("home"))
    client.force_login(data.admin)
    validate_url_get(client, reverse("home"))


def test_home_auth(data, auth_client):
    validate_url_get(auth_client, reverse("home"))


def test_search_empty(data, client):
    validate_url_get(client, reverse("search"))


def test_search_result(data, client):
    validate_url_get(client, reverse("search") + "?34120")


def test_erp_details(data, client):
    validate_url_get(client, data.erp.get_absolute_url())


def test_erp_details_auth(data, auth_client):
    validate_url_get(auth_client, data.erp.get_absolute_url())


def test_editorial_accessibilite(data, client):
    validate_url_get(client, reverse("accessibilite"))


def test_editorial_cgu(data, client):
    validate_url_get(client, reverse("cgu"))


def test_editorial_partenaires(data, client):
    validate_url_get(client, reverse("partenaires"))


def test_login(data, client):
    validate_url_get(client, reverse("login"))
