import sentry_sdk
from django.conf import settings
from django.core.cache import cache
from rest_framework import permissions
from rest_framework_api_key.models import APIKey


class IsAllowedForAction(permissions.BasePermission):
    message = "For internal uses only."

    def has_permission(self, request, view):
        auth = request.META.get("HTTP_AUTHORIZATION")
        if not auth:
            return False

        key = auth.split()[1]
        if key == cache.get(settings.INTERNAL_API_KEY_NAME):
            if view.action in ("default", "list"):
                # Internal api key is allowed to perform only view/list actions, not write operations (create, update, ...)
                return True
            return False

        try:
            with sentry_sdk.start_span(description="Check signature of API KEY"):
                APIKey.objects.get_from_key(key)
        except APIKey.DoesNotExist:
            return False

        return True
