from django.contrib.sites.models import Site

from stats.models import Implementation, Referer


class TrackStatsWidget:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.resolver_match
            and request.resolver_match.url_name == "widget_erp_uuid"
            and request.headers.get("Origin")
            and Site.objects.get_current().domain not in request.headers.get("Origin")
        ):

            try:
                referer, created = Referer.objects.update_or_create(
                    domain=request.headers.get("Origin")
                )
            except Referer.MultipleObjectsReturned:
                qs = Referer.objects.filter(domain=request.headers.get("Origin"))
                last_referer = qs.last()
                qs.exclude(id=last_referer.id).delete()
            try:
                Implementation.objects.update_or_create(
                    urlpath=request.headers.get("X-Originurl")
                    or request.headers.get("Origin"),
                    referer=referer,
                )
            except Implementation.MultipleObjectsReturned:
                qs = Implementation.objects.filter(
                    referer=referer,
                    urlpath=request.headers.get("X-Originurl")
                    or request.headers.get("Origin"),
                )
                last_implementation = qs.latest("updated_at")
                qs.exclude(id=last_implementation.id).delete()
        return response
