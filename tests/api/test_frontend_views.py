import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.test import Client, override_settings
from django.urls import reverse

from tests.factories import ActiviteFactory, CommuneFactory, ErpFactory

GEOJSON = "application/geo+json"


@pytest.fixture
def clear_ratelimit_cache():
    """The test cache is locmem with a fixed LOCATION, shared across the session."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def jacou_erp():
    return ErpFactory(
        nom="Aux bons croissants",
        numero="4",
        voie="grand rue",
        code_postal="34830",
        commune="Jacou",
        activite=ActiviteFactory(nom="Boulangerie"),
        commune_ext=CommuneFactory(nom="Jacou", departement="34", code_insee="34120"),
        geom=Point((3.9047933, 43.6648217)),
        with_accessibility=True,
    )


def features(response):
    return json.loads(response.content)["features"]


@pytest.mark.django_db
class TestFrontendErpList:
    def test_anonymous_gets_geojson(self, client, jacou_erp):
        # No credentials of any kind: this is the whole point of the endpoint.
        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON)

        assert response.status_code == 200
        assert response["Content-Type"].startswith(GEOJSON)
        content = json.loads(response.content)
        assert content["type"] == "FeatureCollection"
        assert content["count"] == 1
        assert "next" in content and "previous" in content
        assert len(content["features"]) == 1

    def test_geojson_is_the_default_representation(self, client, jacou_erp):
        # geo.js and ContribPagination.js send the header, but a bare request must
        # not silently fall back to a different shape.
        response = client.get(reverse("front_erp_list"))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == "FeatureCollection"

    def test_response_matches_frontend_contract(self, client, jacou_erp):
        # Guards static/js/mapUtils.js and static/js/ui/ContribPagination.js.
        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON)

        properties = features(response)[0]["properties"]
        assert set(properties) == {
            "uuid",
            "nom",
            "adresse",
            "commune",
            "activite",
            "web_url",
            "completion_rate",
        }
        assert set(properties["activite"]) == {"nom", "vector_icon"}

    def test_drafts_are_excluded(self, client, jacou_erp):
        draft = ErpFactory(published=False, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON)

        uuids = [feature["properties"]["uuid"] for feature in features(response)]
        assert str(jacou_erp.uuid) in uuids
        assert str(draft.uuid) not in uuids

    def test_with_drafts_param_is_ignored(self, client, jacou_erp):
        draft = ErpFactory(published=False, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"with_drafts": "true"}, HTTP_ACCEPT=GEOJSON)

        uuids = [feature["properties"]["uuid"] for feature in features(response)]
        assert str(draft.uuid) not in uuids
        assert uuids == [str(jacou_erp.uuid)]

    def test_ownerless_drafts_are_excluded(self, client, jacou_erp):
        # The `with_drafts` branch of ErpFilter exposes ownerless drafts to anonymous
        # callers on /api/erps/. It must stay unreachable here.
        ErpFactory(published=False, user=None, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"with_drafts": "true"}, HTTP_ACCEPT=GEOJSON)

        assert json.loads(response.content)["count"] == 1

    def test_filter_by_q(self, client, jacou_erp):
        ErpFactory(nom="Pharmacie du centre", with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"q": "croissants"}, HTTP_ACCEPT=GEOJSON)

        assert [f["properties"]["nom"] for f in features(response)] == ["Aux bons croissants"]

    def test_filter_by_code_insee(self, client, jacou_erp):
        ErpFactory(commune_ext=CommuneFactory(nom="Lyon", code_insee="69123"), with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"code_insee": "34120"}, HTTP_ACCEPT=GEOJSON)

        assert [f["properties"]["nom"] for f in features(response)] == ["Aux bons croissants"]

    def test_filter_by_activite(self, client, jacou_erp):
        ErpFactory(activite=ActiviteFactory(nom="Pharmacie"), with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"activite": "boulangerie"}, HTTP_ACCEPT=GEOJSON)

        assert [f["properties"]["nom"] for f in features(response)] == ["Aux bons croissants"]

    def test_filter_by_zone(self, client, jacou_erp):
        ErpFactory(geom=Point((2.3522, 48.8566)), with_accessibility=True)  # Paris

        response = client.get(reverse("front_erp_list"), {"zone": "3.8,43.6,4.0,43.7"}, HTTP_ACCEPT=GEOJSON)

        assert [f["properties"]["nom"] for f in features(response)] == ["Aux bons croissants"]

    def test_filter_by_equipments(self, client):
        with_transport = ErpFactory(with_accessibility=True, accessibilite__transport_station_presence=True)
        ErpFactory(with_accessibility=True, accessibilite__transport_station_presence=False)

        response = client.get(
            reverse("front_erp_list"),
            {"equipments": "having_public_transportation"},
            HTTP_ACCEPT=GEOJSON,
        )

        uuids = [f["properties"]["uuid"] for f in features(response)]
        assert uuids == [str(with_transport.uuid)]

    def test_unknown_params_are_ignored(self, client, jacou_erp):
        # Proves the allow-list, and that ErpFilter's `distinct("id", "nom")` path
        # (which conflicts with the trailing order_by) stays unreachable here.
        response = client.get(
            reverse("front_erp_list"),
            {
                "source": "gendarmerie",
                "created_or_updated_in_last_days": "1",
                "asp_id_not_null": "true",
                "commune": "nowhere",
            },
            HTTP_ACCEPT=GEOJSON,
        )

        assert response.status_code == 200
        assert json.loads(response.content)["count"] == 1

    def test_page_size_default(self, client):
        ErpFactory.create_batch(25, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON)

        assert len(features(response)) == 20

    def test_page_size_is_capped(self, client):
        ErpFactory.create_batch(25, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"page_size": 1000}, HTTP_ACCEPT=GEOJSON)

        assert len(features(response)) == 25  # capped at 100, only 25 exist
        assert json.loads(response.content)["next"] is None

    def test_page_size_below_the_cap_is_honoured(self, client):
        ErpFactory.create_batch(10, with_accessibility=True)

        response = client.get(reverse("front_erp_list"), {"page_size": 6}, HTTP_ACCEPT=GEOJSON)

        assert len(features(response)) == 6
        assert json.loads(response.content)["next"] is not None

    def test_completion_rate_without_accessibilite(self, client):
        ErpFactory()  # no Accessibilite row

        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON)

        assert response.status_code == 200
        assert features(response)[0]["properties"]["completion_rate"] is None

    @pytest.mark.parametrize(
        "sec_fetch_site, expected",
        [("cross-site", 403), ("same-origin", 200), ("same-site", 200), ("none", 200)],
    )
    def test_sec_fetch_site(self, client, jacou_erp, sec_fetch_site, expected):
        response = client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON, HTTP_SEC_FETCH_SITE=sec_fetch_site)

        assert response.status_code == expected

    def test_missing_sec_fetch_site_is_allowed(self, client, jacou_erp):
        # Old browsers don't send the header; blocking them would gain nothing.
        assert client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON).status_code == 200

    def test_api_key_is_not_required(self, client, jacou_erp):
        assert client.get(reverse("front_erp_list"), HTTP_ACCEPT=GEOJSON).status_code == 200

    @override_settings(FRONT_SEARCH_ERPS_RATE="2/m", RATELIMIT_ENABLE=True)
    def test_rate_limited_by_ip(self, client, jacou_erp, clear_ratelimit_cache):
        url = reverse("front_erp_list")

        assert client.get(url, HTTP_ACCEPT=GEOJSON).status_code == 200
        assert client.get(url, HTTP_ACCEPT=GEOJSON).status_code == 200

        response = client.get(url, HTTP_ACCEPT=GEOJSON)
        assert response.status_code == 429
        assert response.has_header("Retry-After")

        # Another IP keeps its own bucket.
        other = client.get(url, HTTP_ACCEPT=GEOJSON, REMOTE_ADDR="10.0.0.1")
        assert other.status_code == 200


@pytest.mark.django_db
class TestFrontendTranslate:
    @pytest.fixture
    def erp(self):
        return ErpFactory(with_accessibility=True, accessibilite__commentaire="foo")

    def _url(self, erp):
        return reverse("front_accessibility_translate", kwargs={"pk": erp.accessibilite.pk})

    def _post(self, client, erp, payload, **extra):
        return client.post(self._url(erp), data=json.dumps(payload), content_type="application/json", **extra)

    def test_translate_success(self, client, erp):
        mock_result = MagicMock()
        mock_result.text = "The entrance is accessible via a removable ramp."
        mock_translator = MagicMock()
        mock_translator.translate_text.return_value = mock_result

        with patch("erp.provider.deepl.Translator", return_value=mock_translator):
            response = self._post(client, erp, {"field": "commentaire", "target_lang": "en"})

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["field"] == "commentaire"
        assert content["target_lang"] == "en"
        assert content["original"] == erp.accessibilite.commentaire
        assert content["translated"] == "The entrance is accessible via a removable ramp."

    def test_translate_empty_field(self, client, erp):
        erp.accessibilite.commentaire = None
        erp.accessibilite.save()

        mock_translator = MagicMock()
        with patch("erp.provider.deepl.Translator", return_value=mock_translator):
            response = self._post(client, erp, {"field": "commentaire", "target_lang": "en"})
            mock_translator.assert_not_called()

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["translated"] is None
        assert content["original"] is None

    def test_translate_invalid_field(self, client, erp):
        response = self._post(client, erp, {"field": "non_translatable_field", "target_lang": "en"})

        assert response.status_code == 400

    def test_translate_missing_target_lang(self, client, erp):
        response = self._post(client, erp, {"field": "commentaire"})

        assert response.status_code == 400

    def test_translate_invalid_body(self, client, erp):
        response = client.post(self._url(erp), data="not json", content_type="application/json")

        assert response.status_code == 400

    def test_translate_unknown_accessibilite(self, client):
        response = client.post(
            reverse("front_accessibility_translate", kwargs={"pk": 99999}),
            data=json.dumps({"field": "commentaire", "target_lang": "en"}),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_translate_unpublished_erp(self, client):
        draft = ErpFactory(published=False, with_accessibility=True, accessibilite__commentaire="foo")

        response = self._post(client, draft, {"field": "commentaire", "target_lang": "en"})

        assert response.status_code == 404

    def test_get_not_allowed(self, client, erp):
        assert client.get(self._url(erp)).status_code == 405

    def test_cross_site_is_rejected(self, client, erp):
        response = self._post(
            client, erp, {"field": "commentaire", "target_lang": "en"}, HTTP_SEC_FETCH_SITE="cross-site"
        )

        assert response.status_code == 403

    def test_csrf_token_is_required(self, erp):
        # This is what a DRF APIView could not give us: APIView.as_view() is
        # csrf_exempt, and SessionAuthentication only enforces CSRF for logged-in users.
        csrf_client = Client(enforce_csrf_checks=True)
        payload = json.dumps({"field": "commentaire", "target_lang": "en"})

        assert csrf_client.post(self._url(erp), data=payload, content_type="application/json").status_code == 403

        request = csrf_client.get(reverse("home")).wsgi_request
        token = get_token(request)
        mock_result = MagicMock()
        mock_result.text = "translated"
        with patch("erp.provider.deepl.Translator", return_value=MagicMock(translate_text=lambda *a, **k: mock_result)):
            response = csrf_client.post(
                self._url(erp), data=payload, content_type="application/json", HTTP_X_CSRFTOKEN=token
            )

        assert response.status_code == 200

    @override_settings(FRONT_TRANSLATE_RATE="1/m", RATELIMIT_ENABLE=True)
    def test_rate_limited_by_ip(self, client, erp, clear_ratelimit_cache):
        payload = {"field": "commentaire", "target_lang": "en"}
        mock_result = MagicMock()
        mock_result.text = "translated"

        with patch(
            "erp.provider.deepl.Translator",
            return_value=MagicMock(translate_text=lambda *a, **k: mock_result),
        ):
            assert self._post(client, erp, payload).status_code == 200
            limited = self._post(client, erp, payload)

        assert limited.status_code == 429
        assert limited["Retry-After"] == "60"
