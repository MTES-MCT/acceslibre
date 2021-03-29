import pytest

from django.test import Client
from django.urls import reverse

from erp.models import Activite


@pytest.mark.django_db
def test_home():
    c = Client()
    Activite.objects.create(nom="Centre de vaccination")
    response = c.get(reverse("stats_home"))
    assert response.status_code == 200
