import datetime
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIRequestFactory
from rest_framework_api_key.models import APIKey

from api.permissions import IsAllowedForAction
from erp.views import _get_or_create_api_key


@pytest.mark.django_db
class TestPermissions:
    perm = IsAllowedForAction()
    factory = APIRequestFactory()

    def test_bad_key_value(self):
        request = self.factory.get("/", headers={"Authorization": "Api-Key FOO"})

        assert self.perm.has_permission(request, MagicMock(action="list")) is False

    def test_bad_key_format(self):
        request = self.factory.get("/", headers={"Authorization": "FOO"})

        assert self.perm.has_permission(request, MagicMock(action="list")) is False

    def test_internal_key_for_get(self, settings):
        cache_settings = settings.CACHES.copy()
        cache_settings["default"]["BACKEND"] = "django.core.cache.backends.locmem.LocMemCache"
        settings.CACHES = cache_settings

        internal_key = _get_or_create_api_key()
        assert internal_key, "None or empty internal key generated."
        request = self.factory.get("/", headers={"Authorization": f"Api-Key {internal_key}"})

        assert self.perm.has_permission(request, MagicMock(action="list")) is True

    def test_internal_key_for_post(self, settings):
        cache_settings = settings.CACHES.copy()
        cache_settings["default"]["BACKEND"] = "django.core.cache.backends.locmem.LocMemCache"
        settings.CACHES = cache_settings

        internal_key = _get_or_create_api_key()
        assert internal_key, "None or empty internal key generated."
        request = self.factory.get("/", headers={"Authorization": f"Api-Key {internal_key}"})

        assert self.perm.has_permission(request, MagicMock(action="delete")) is False

    def test_api_key(self, settings):
        _, api_key = APIKey.objects.create_key(
            name=settings.INTERNAL_API_KEY_NAME, expiry_date=datetime.datetime.now() + datetime.timedelta(hours=1.2)
        )

        request = self.factory.get("/", headers={"Authorization": f"Api-Key {api_key}"})

        assert self.perm.has_permission(request, MagicMock(action="list")) is True
