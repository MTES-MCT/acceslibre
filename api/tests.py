import pytest

from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, status_code",
    [
        ("openapi-schema", 200),
        ("apidocs", 200),
        ("api-root", 200),
        ("accessibilite-list", 200),
        ("accessibilite-help", 200),
        ("activite-list", 200),
        ("erp-list", 200),
    ],
)
def test_api_urls_ok(url, status_code, api_client):
    response = api_client.get(reverse(url))
    assert response.status_code == status_code
