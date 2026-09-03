import datetime

from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIRequestFactory
from rest_framework_api_key.models import APIKey

from compte.models import UserAPIKey
from api.permissions import IsAllowedForAction
from tests.factories import UserFactory


@pytest.mark.django_db
class TestPermissions:
    perm = IsAllowedForAction()
    factory = APIRequestFactory()

    def _request_with_auth(self, header=None, auth=None):
        """Builds a request as DRF would present it to a permission:
        raw WSGIRequest + `.auth` populated by authentication (or None
        if no authenticator matched, mirroring DRF's default)."""
        kwargs = {"headers": {"Authorization": header}} if header else {}
        request = self.factory.get("/", **kwargs)
        request.auth = auth
        return request

    def test_no_header(self):
        request = self._request_with_auth()

        assert self.perm.has_permission(request, MagicMock(action="list")) is False

    def test_bad_key_format(self):
        request = self._request_with_auth(header="FOO")

        assert self.perm.has_permission(request, MagicMock(action="list")) is False

    def test_bad_key_value(self):
        request = self._request_with_auth(header="Api-Key FOO")

        assert self.perm.has_permission(request, MagicMock(action="list")) is False

    def test_legacy_api_key_grants_access(self):
        _, api_key = APIKey.objects.create_key(
            name="new-key", expiry_date=datetime.datetime.now() + datetime.timedelta(hours=1.2)
        )
        request = self._request_with_auth(header=f"Api-Key {api_key}")

        assert self.perm.has_permission(request, MagicMock(action="list")) is True

    def test_user_api_key_grants_access(self):
        user = UserFactory()
        api_key_instance, key = UserAPIKey.objects.create_key(name="user-key", user=user)
        request = self._request_with_auth(header=f"Api-Key {key}", auth=api_key_instance)

        assert self.perm.has_permission(request, MagicMock(action="list")) is True
