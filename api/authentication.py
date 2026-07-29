from rest_framework.authentication import BaseAuthentication

from compte.models import UserAPIKey


class UserAPIKeyAuthentication(BaseAuthentication):
    """New API Key system, linked to a user. Return None if not found to fallback on legacy system."""

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION")
        if not auth:
            return None

        parts = auth.split()
        if len(parts) != 2:
            return None

        key = parts[1]
        try:
            api_key = UserAPIKey.objects.get_from_key(key)
        except UserAPIKey.DoesNotExist:
            return None

        return (api_key.user, api_key)
