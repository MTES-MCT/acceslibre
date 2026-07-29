import sentry_sdk
from django.utils.translation import gettext as translate
from rest_framework import permissions
from rest_framework_api_key.models import APIKey

from compte.models import UserAPIKey

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class IsAllowedForAction(permissions.BasePermission):
    message = "For internal uses only."

    def has_permission(self, request, view):
        auth = request.META.get("HTTP_AUTHORIZATION")
        if not auth:
            return False

        if len(auth_split := auth.split()) != 2:
            return False

        key = auth_split[1]

        if isinstance(request.auth, UserAPIKey):
            return True

        try:
            with sentry_sdk.start_span(description="Check signature of API KEY"):
                APIKey.objects.get_from_key(key)
        except APIKey.DoesNotExist:
            return False

        return True


class CanModifyErp(permissions.BasePermission):
    message = translate("Cet établissement est labellisé RPA et ne peut être modifié que par son gestionnaire.")

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.can_be_modified_by(request.user)
