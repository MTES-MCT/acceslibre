import pytest

from django.test import Client
from django.urls import reverse

from ..models import Commune, Erp


@pytest.mark.django_db
def test_home():
    c = Client()
    response = c.get(reverse("home"))
    assert response.status_code == 200
