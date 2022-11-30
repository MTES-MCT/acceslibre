import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from stats.models import GlobalStats, Implementation, Referer


@pytest.mark.django_db
def test_widget_tracking(data):
    c = Client()
    headers = {
        "HTTP_ORIGIN": "http://test_widget_external_website.tld",
        "HTTP_X-Originurl": "http://test_widget_external_website.tld/test_url.php",
    }
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 1
    assert Implementation.objects.all().count() == 1
    impl = Implementation.objects.last()
    assert impl.urlpath == "http://test_widget_external_website.tld/test_url.php"


@pytest.mark.django_db
def test_widget_tracking_without_origin(data):
    c = Client()
    headers = {
        "HTTP_REFERER": "http://test_widget_external_website.tld",
        "HTTP_X-Originurl": "http://test_widget_external_website.tld",
    }
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 0


@pytest.mark.django_db
def test_widget_tracking_with_same_origin_site(data):
    c = Client()
    headers = {
        "HTTP_REFERER": "http://%s" % Site.objects.get_current().domain,
        "HTTP_X-Originurl": "http://test_widget_external_website.tld",
    }
    assert Referer.objects.all().count() == 0
    response = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response.status_code == 200
    assert Referer.objects.all().count() == 0


@pytest.mark.django_db
def test_widget_tracking_verify_dupes(data):
    c = Client()
    headers = {
        "HTTP_ORIGIN": "http://test_widget_external_website.tld",
        "HTTP_X-Originurl": "http://test_widget_external_website.tld/test_url.php",
    }
    assert Referer.objects.all().count() == 0
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers)
    response_dupes = c.get(
        reverse("widget_erp_uuid", kwargs={"uuid": data.erp.uuid}), **headers
    )
    assert response_dupes.status_code == 200
    assert Referer.objects.all().count() == 1
    assert Implementation.objects.all().count() == 1
    impl = Implementation.objects.last()
    assert impl.urlpath == "http://test_widget_external_website.tld/test_url.php"


def test_command_refresh_stats(client, data, mocker):
    call_command("refresh_global_stats")
    assert GlobalStats.objects.count() == 1
    stat = GlobalStats.objects.get()
    assert stat.top_contributors is not dict()
