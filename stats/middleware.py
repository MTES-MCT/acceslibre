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
        ):

            referer, created = Referer.objects.update_or_create(
                domain=request.headers.get("Origin")
            )
            Implementation.objects.update_or_create(
                urlpath=request.headers.get("Referer") or request.headers.get("Origin"),
                referer=referer,
            )
        return response
