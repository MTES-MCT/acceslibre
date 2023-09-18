import datetime
from urllib.parse import urlparse

from django.contrib.sites.models import Site
from django.db.models import F

from .models import WidgetEvent


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
        domain = urlparse(referer).netloc or referer
        date = datetime.date.today()

        event, _ = WidgetEvent.objects.get_or_create(date=date, domain=domain, referer_url=referer)
        event.views = F("views") + 1
        event.save()

    def __call__(self, request):
        response = self.get_response(request)

        if not self._should_track_request(request):
            return response

        self._update_event(request)

        return response
