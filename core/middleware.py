import sentry_sdk


class SentryUserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            sentry_sdk.set_user({"username": request.user.username})
        return self.get_response(request)
