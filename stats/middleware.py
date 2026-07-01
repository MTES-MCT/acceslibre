import datetime
from urllib.parse import urljoin, urlparse

from django.contrib.sites.models import Site
from django.core.cache import cache


class TrackStatsWidget:
    def __init__(self, get_response):
        self.get_response = get_response

    def _should_track_request(self, request):
        return (
            request.resolver_match
            and request.resolver_match.url_name == "widget_erp_uuid"
            and request.headers.get("X-OriginUrl")
            and Site.objects.get_current().domain not in request.headers.get("X-OriginUrl")
        )

    def _update_event(self, request):
        referer = request.headers.get("X-OriginUrl")
        referer = referer[:199]
        referer = urljoin(referer, urlparse(referer).path)
        domain = urlparse(referer).netloc or referer
        date_str = datetime.date.today().isoformat()

        # Create a unique key for Redis with prefix to avoid collisions
        # format: stats_widget:2023-10-27:example.com:https://example.com/page
        redis_key = f"stats_widget:{date_str}:{domain}:{referer}"

        try:
            cache.incr(redis_key)
        except ValueError:
            cache.set(redis_key, 1, timeout=None)

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_track_request(request):
            self._update_event(request)
        return response
