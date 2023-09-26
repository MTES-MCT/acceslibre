import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from stats.models import GlobalStats, WidgetEvent


@pytest.mark.django_db
def test_widget_tracking(data):
    c = Client()
    headers = {
        "HTTP_X-Originurl": "http://test_widget_external_website.tld/test_url.php",
    }
    assert WidgetEvent.objects.all().count() == 0
    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    assert response.status_code == 200

    event = WidgetEvent.objects.get()
    assert event.views == 1
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url == "http://test_widget_external_website.tld/test_url.php"


@pytest.mark.django_db
def test_widget_tracking_with_long_url(data):
    c = Client()
    headers = {
        "HTTP_X-Originurl": "http://test_widget_external_website.tld/?utm=" + 200 * "#",
    }
    assert WidgetEvent.objects.all().count() == 0
    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    assert response.status_code == 200

    event = WidgetEvent.objects.get()
    assert event.views == 1
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url.startswith("http://test_widget_external_website.tld/?utm=")


@pytest.mark.django_db
def test_widget_tracking_multiple_views(data):
    c = Client()
    headers = {
        "HTTP_X-Originurl": "http://test_widget_external_website.tld/test_url.php",
    }
    assert WidgetEvent.objects.all().count() == 0
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)

    event = WidgetEvent.objects.get()
    assert event.views == 3
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url == "http://test_widget_external_website.tld/test_url.php"


@pytest.mark.django_db
def test_widget_tracking_with_same_origin_site(data):
    c = Client()
    headers = {
        "HTTP_X-Originurl": f"http://{Site.objects.get_current().domain}/test/",
    }
    assert WidgetEvent.objects.all().count() == 0
    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    assert response.status_code == 200
    assert WidgetEvent.objects.all().count() == 0


def test_command_refresh_stats(client, data):
    call_command("refresh_stats")
    assert GlobalStats.objects.count() == 1
    stat = GlobalStats.objects.get()
    assert stat.top_contributors is not dict()
