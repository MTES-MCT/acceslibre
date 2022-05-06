import pytest
from django.contrib.sites.models import Site

from django.test import Client
from django.urls import reverse

from stats.models import Referer


@pytest.mark.django_db
def test_widget_tracking(data):
    c = Client()
    headers = {"HTTP_ORIGIN": "http://test_widget_external_website.tld"}
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 1


@pytest.mark.django_db
def test_widget_tracking_without_origin(data):
    c = Client()
    headers = {"HTTP_REFERER": "http://test_widget_external_website.tld"}
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 0


@pytest.mark.django_db
def test_widget_tracking_with_same_origin_site(data):
    c = Client()
    headers = {"HTTP_REFERER": "http://%s" % Site.objects.get_current().domain}
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 0
