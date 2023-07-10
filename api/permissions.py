import sentry_sdk
from django.conf import settings
from rest_framework import permissions
from rest_framework_api_key.models import APIKey


class IsAllowedForAction(permissions.BasePermission):
    message = "For internal uses only."

    def has_permission(self, request, view):
        auth = request.META.get("HTTP_AUTHORIZATION")
        if not auth:
            return False

        key = auth.split()[1]
        try:
            with sentry_sdk.start_span(description="Check signature of API KEY"):
                api_key = APIKey.objects.get_from_key(key)
        except APIKey.DoesNotExist:
            return False

        if api_key.name == settings.INTERNAL_API_KEY_NAME and view.action not in ("default", "list"):
            # Internal api key is allowed to perform only view/list actions, not write operations (create, update, ...)
            return False

        return True
