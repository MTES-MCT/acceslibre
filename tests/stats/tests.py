import pickle
from unittest.mock import MagicMock, call, patch

import pytest
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from splinter import Browser

from stats.models import WidgetEvent
from stats.queries import _get_nb_filled_in_info
from tests.factories import ErpFactory


@pytest.fixture
def browser():
    return Browser("django")


@pytest.fixture(autouse=True)
def setup_redis_mock():
    with patch("redis.from_url") as mock_redis_from_url:
        fake_redis = MagicMock()

        def mock_scan_iter(match):
            # Scan keys in Django's LocMemCache
            return [k.encode() if isinstance(k, str) else k for k in cache._cache.keys() if "stats_widget" in k]

        def mock_pipeline():
            pipe = MagicMock()
            stored_keys = []

            def pipe_get(key):
                stored_keys.append(key.decode() if isinstance(key, bytes) else key)
                return pipe

            def pipe_execute():
                results = []
                for key in stored_keys:
                    raw_val = cache._cache.get(key)
                    if raw_val is None:
                        results.append(None)
                        continue

                    # Handle Django's internal Pickle serialization in LocMemCache
                    try:
                        if isinstance(raw_val, bytes) and raw_val.startswith(b"\x80"):
                            val = pickle.loads(raw_val)
                        else:
                            val = raw_val
                    except Exception:
                        val = raw_val

                    # Return bytes-string to simulate redis-py behavior for int(val)
                    results.append(str(val).encode())

                    if key in cache._cache:
                        del cache._cache[key]

                return [results[0] if results else None, True]

            pipe.get.side_effect = pipe_get
            pipe.execute.side_effect = pipe_execute
            return pipe

        fake_redis.scan_iter.side_effect = mock_scan_iter
        fake_redis.pipeline.side_effect = mock_pipeline
        mock_redis_from_url.return_value = fake_redis
        yield mock_redis_from_url


@pytest.mark.django_db
@patch("stats.matomo.requests.post")
def test_stats_page(mocked, browser, django_assert_max_num_queries):
    mocked.side_effect = MagicMock(status_code=200, json=lambda: {})
    with django_assert_max_num_queries(8):
        browser.visit(reverse("stats_home"))

    assert mocked.call_count == 2

    get_visitors = call(
        "https://stats.beta.gouv.fr/index.php",
        data={
            "module": "API",
            "idSite": 3,
            "period": "day",
            "date": "last30",
            "format": "JSON",
            "token_auth": "YYYY",
            "method": "VisitsSummary.getUniqueVisitors",
        },
        timeout=2,
    )
    assert mocked.mock_calls[0] == get_visitors
    get_actions = call(
        "https://acceslibre.matomo.cloud/index.php",
        data={
            "module": "API",
            "idSite": 1,
            "period": "day",
            "date": "last30",
            "format": "JSON",
            "token_auth": "XXXX",
            "method": "Events.getAction",
        },
        timeout=2,
    )
    assert mocked.mock_calls[1] == get_actions


@pytest.mark.django_db
def test_widget_tracking(setup_redis_mock):
    cache.clear()
    erp = ErpFactory(with_accessibility=True)
    c = Client()
    headers = {
        "HTTP_X_Originurl": "http://test_widget_external_website.tld/test_url.php",
    }

    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    assert response.status_code == 200

    call_command("flush_widget_stats")

    event = WidgetEvent.objects.get(domain="test_widget_external_website.tld")
    assert event.views == 1
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url == "http://test_widget_external_website.tld/test_url.php"


@pytest.mark.django_db
def test_widget_tracking_with_long_url(setup_redis_mock):
    cache.clear()
    erp = ErpFactory(with_accessibility=True)
    c = Client()
    headers = {
        "HTTP_X_Originurl": "http://test_widget_external_website.tld/" + 210 * "a",
    }

    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    assert response.status_code == 200

    call_command("flush_widget_stats")

    event = WidgetEvent.objects.get()
    assert event.views == 1
    assert event.domain == "test_widget_external_website.tld"


@pytest.mark.django_db
def test_widget_tracking_remove_query_string(setup_redis_mock):
    cache.clear()
    erp = ErpFactory(with_accessibility=True)
    c = Client()
    headers = {"HTTP_X_Originurl": "http://test_widget_external_website.tld/path/?utm=foo"}

    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    assert response.status_code == 200

    call_command("flush_widget_stats")

    event = WidgetEvent.objects.get()
    assert event.views == 1
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url == "http://test_widget_external_website.tld/path/"


@pytest.mark.django_db
def test_widget_tracking_multiple_views(setup_redis_mock):
    cache.clear()
    erp = ErpFactory(with_accessibility=True)
    c = Client()
    headers = {
        "HTTP_X_Originurl": "http://test_widget_external_website.tld/test_url.php",
    }

    c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)

    call_command("flush_widget_stats")

    event = WidgetEvent.objects.get()
    assert event.views == 3
    assert event.domain == "test_widget_external_website.tld"
    assert event.referer_url == "http://test_widget_external_website.tld/test_url.php"


@pytest.mark.django_db
def test_widget_tracking_with_same_origin_site(setup_redis_mock):
    cache.clear()
    erp = ErpFactory(with_accessibility=True)
    c = Client()
    headers = {
        "HTTP_X_Originurl": f"http://{Site.objects.get_current().domain}/test/",
    }

    response = c.get(reverse("widget_erp_uuid", kwargs={"uuid": erp.uuid}), **headers)
    assert response.status_code == 200

    call_command("flush_widget_stats")
    assert WidgetEvent.objects.all().count() == 0


def test_get_nb_filled_in_infos():
    initial = {
        "erp": 252060,
        "transport_station_presence": None,
        "transport_information": None,
        "stationnement_presence": True,
        "stationnement_pmr": True,
        "stationnement_ext_presence": None,
        "stationnement_ext_pmr": None,
        "cheminement_ext_presence": None,
        "cheminement_ext_plain_pied": None,
        "cheminement_ext_terrain_stable": None,
        "cheminement_ext_nombre_marches": None,
        "cheminement_ext_sens_marches": None,
        "cheminement_ext_reperage_marches": None,
        "cheminement_ext_main_courante": None,
        "cheminement_ext_rampe": None,
        "cheminement_ext_ascenseur": None,
        "cheminement_ext_pente_presence": None,
        "cheminement_ext_pente_degre_difficulte": None,
        "cheminement_ext_pente_longueur": None,
        "cheminement_ext_devers": None,
        "cheminement_ext_bande_guidage": None,
        "cheminement_ext_retrecissement": None,
        "entree_reperage": None,
        "entree_porte_presence": None,
        "entree_porte_manoeuvre": None,
        "entree_porte_type": None,
        "entree_vitree": None,
        "entree_vitree_vitrophanie": None,
        "entree_plain_pied": None,
        "entree_marches": None,
        "entree_marches_sens": None,
        "entree_marches_reperage": None,
        "entree_marches_main_courante": None,
        "entree_marches_rampe": None,
        "entree_balise_sonore": None,
        "entree_dispositif_appel": None,
        "entree_dispositif_appel_type": None,
        "entree_aide_humaine": None,
        "entree_ascenseur": None,
        "entree_largeur_mini": None,
        "entree_pmr": None,
        "entree_pmr_informations": None,
        "accueil_visibilite": None,
        "accueil_personnels": None,
        "accueil_audiodescription_presence": None,
        "accueil_audiodescription": None,
        "accueil_equipements_malentendants_presence": None,
        "accueil_equipements_malentendants": None,
        "accueil_cheminement_plain_pied": True,
        "accueil_cheminement_nombre_marches": None,
        "accueil_cheminement_sens_marches": None,
        "accueil_cheminement_reperage_marches": None,
        "accueil_cheminement_main_courante": None,
        "accueil_cheminement_rampe": None,
        "accueil_cheminement_ascenseur": None,
        "accueil_retrecissement": False,
        "accueil_chambre_nombre_accessibles": None,
        "accueil_chambre_douche_plain_pied": None,
        "accueil_chambre_douche_siege": None,
        "accueil_chambre_douche_barre_appui": None,
        "accueil_chambre_sanitaires_barre_appui": None,
        "accueil_chambre_sanitaires_espace_usage": None,
        "accueil_chambre_numero_visible": None,
        "accueil_chambre_equipement_alerte": None,
        "accueil_chambre_accompagnement": None,
        "sanitaires_presence": True,
        "sanitaires_adaptes": True,
        "labels": None,
        "labels_familles_handicap": None,
        "labels_autre": None,
        "commentaire": "blah",
        "registre_url": None,
        "conformite": None,
        "created_at": "2023-11-20T10:28:25.903Z",
        "updated_at": "2023-11-20T10:28:25.903Z",
    }
    assert _get_nb_filled_in_info(initial) == 6

    initial["commentaire"] = "this should be ignored"
    assert _get_nb_filled_in_info(initial) == 6

    initial["accueil_retrecissement"] = None
    assert _get_nb_filled_in_info(initial) == 5

    initial["entree_dispositif_appel"] = True
    initial["entree_dispositif_appel_type"] = ["interphone"]
    assert _get_nb_filled_in_info(initial) == 7

    initial["entree_dispositif_appel_type"] = ["interphone", "visiophone"]
    assert _get_nb_filled_in_info(initial) == 7
