from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class AdminCSRFCookieMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith("/admin/"):
            csrf_cookie_name = settings.CSRF_COOKIE_NAME
            if csrf_cookie_name in response.cookies:
                response.cookies[csrf_cookie_name]["httponly"] = False
        return response
