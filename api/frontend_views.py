"""Endpoints consumed by acceslibre's own frontend JS.

They live in the `api` package because they reuse its filters, serializers and
renderers, but they are deliberately mounted *outside* `/api/`: everything under
`/api/` now requires an `Authorization: Api-Key` header, and we will not ship a
key in frontend JS.

What protects them instead:
  - they are not listed in `CORS_URLS_REGEX`, so no browser on another origin can
    read their responses (and the translate endpoint further requires a CSRF
    token, which is same-origin by construction);
  - a per-IP rate limit (django-ratelimit, Redis-backed);
  - a capped page size, an allow-list of query parameters, published
    establishments only, and read-only payloads.

None of this is an authentication boundary: `curl` ignores CORS. It is what keeps
casual scraping and DeepL quota burning off the frontend surface.
"""

import contextlib
import json

from deepl import QuotaExceededException
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as translate_
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework_gis.pagination import GeoJsonPagination

from api.filters import EquipmentFilter, PublishedErpFilter, ZoneFilter
from api.renderers import GeoJSONRenderer
from api.serializers import ErpGeoSerializer
from core.utils import real_ip_key
from erp.imports.serializers import TranslateSerializer
from erp.models import Accessibilite, Erp
from erp.provider.deepl import translate as translator

#: Query parameters our own JS actually sends (static/js/geo.js and
#: static/js/ui/ContribPagination.js). Anything else is dropped before the filter
#: backends see it: it keeps this endpoint a *search* surface rather than a bulk
#: extraction one, and it keeps `with_drafts`, `created_or_updated_in_last_days`,
#: `source` and `asp_id_not_null` exclusively on the authenticated `/api/erps/`.
FRONTEND_QUERY_PARAMS = frozenset(
    {"q", "zone", "page", "page_size", "sortType", "where", "equipments", "code_insee", "activite"}
)


#: Suffixes accepted in a django-ratelimit rate, e.g. "120/m" or "100/5m".
_RATE_PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _erps_rate(group, request):
    # Resolved per request so the limit can be retuned through settings (and
    # overridden in tests) without touching the decorator.
    return settings.FRONT_ERPS_RATE


def _translate_rate(group, request):
    return settings.FRONT_TRANSLATE_RATE


def retry_after(rate):
    """Window length of a django-ratelimit rate, in seconds.

    django-ratelimit does not surface how long the bucket stays full, so we answer
    with the whole window: an upper bound, which is the safe direction for a
    `Retry-After`.
    """
    _, _, period = rate.partition("/")
    multiplier = period[:-1] or "1"
    return int(multiplier) * _RATE_PERIODS[period[-1]]


def reject_cross_site(request):
    """Defence in depth, *not* a security boundary.

    Browsers send `Sec-Fetch-Site` on every fetch/XHR, so a cross-site one can be
    rejected before it costs us a query. Requests without the header (older
    browsers, curl, server-side clients) are let through on purpose: blocking them
    would break legacy browsers without inconveniencing anyone able to set headers.
    """
    return request.META.get("HTTP_SEC_FETCH_SITE") == "cross-site"


class FrontendGeoJsonPagination(GeoJsonPagination):
    # GeoJsonPagination defines neither, so without these `?page_size=` is honoured
    # with no upper bound at all.
    page_size = 20
    max_page_size = 100  # the frontend never asks for more than 20


@method_decorator(
    ratelimit(key=real_ip_key, rate=_erps_rate, method="GET", block=False),
    name="dispatch",
)
class FrontendErpListView(ListAPIView):
    """geoJSON feed behind the search map and the contribution search.

    Response shape is what `/api/erps/` returns with `Accept: application/geo+json`:
    same serializer, same pagination envelope.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = []  # per-IP limiting is django-ratelimit's job here
    renderer_classes = [GeoJSONRenderer, JSONRenderer]
    serializer_class = ErpGeoSerializer
    pagination_class = FrontendGeoJsonPagination
    filter_backends = (ZoneFilter, EquipmentFilter, PublishedErpFilter)
    bbox_filter_field = "geom"
    schema = None  # not part of the documented public API

    def get_queryset(self):
        # commune_ext is needed by Erp.commune_slug -> get_absolute_uri(), which the
        # serializer calls for every feature.
        return Erp.objects.published().select_related("activite", "accessibilite", "commune_ext")

    def initial(self, request, *args, **kwargs):
        if reject_cross_site(request):
            raise PermissionDenied(translate_("Requête inter-site refusée."))

        if getattr(request, "limited", False):
            raise Throttled(
                wait=retry_after(settings.FRONT_ERPS_RATE),
                detail=translate_("Trop de requêtes, merci de réessayer dans un instant."),
            )

        # Drop every parameter the frontend does not send. `request.query_params` is
        # `request._request.GET`, so both filter backends see the trimmed mapping.
        params = request.query_params.copy()
        for key in set(params) - FRONTEND_QUERY_PARAMS:
            del params[key]
        params._mutable = False
        request._request.GET = params

        super().initial(request, *args, **kwargs)


@require_POST
@ratelimit(key=real_ip_key, rate=_translate_rate, method="POST", block=False)
def translate_accessibilite_field(request, pk):
    """Called by TranslateField.js on establishment pages viewed in a non-French locale.

    Plain Django view on purpose: `CsrfViewMiddleware` then applies to every caller,
    whereas a DRF `APIView` is csrf_exempt and `SessionAuthentication` only enforces
    CSRF for already-logged-in users. Each call costs DeepL quota, hence the tight
    per-IP limit.
    """
    if reject_cross_site(request):
        return JsonResponse({"detail": translate_("Requête inter-site refusée.")}, status=403)

    if getattr(request, "limited", False):
        response = JsonResponse(
            {"detail": translate_("Trop de traductions demandées, merci de réessayer plus tard.")},
            status=429,
        )
        response["Retry-After"] = retry_after(settings.FRONT_TRANSLATE_RATE)
        return response

    accessibilite = get_object_or_404(Accessibilite.objects.select_related("erp").filter(erp__published=True), pk=pk)

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": translate_("Corps de requête invalide.")}, status=400)

    serializer = TranslateSerializer(data=payload)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    field = serializer.validated_data["field"]
    target_lang = serializer.validated_data["target_lang"]

    original = getattr(accessibilite, field, None)
    if not original:
        return JsonResponse({"translated": None, "original": None})

    translated = original
    if target_lang != settings.LANGUAGE_CODE:
        with contextlib.suppress(QuotaExceededException):
            translated = translator(original, target_lang)

    return JsonResponse(
        {
            "field": field,
            "original": original,
            "translated": translated,
            "target_lang": target_lang,
        }
    )
