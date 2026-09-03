from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class FrontendOriginThrottle(SimpleRateThrottle):
    """Generous quota for requests that appear to come from our own
    frontend. Not a security mechanism (Origin/Referer are spoofable):
    it only avoids penalizing normal site usage while pushing
    unregistered scraping toward requesting an API key."""

    scope = "frontend"

    def get_cache_key(self, request, view):
        origin = request.META.get("HTTP_ORIGIN") or request.META.get("HTTP_REFERER", "")
        if not origin.startswith(settings.SITE_ROOT_URL):
            return None
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
