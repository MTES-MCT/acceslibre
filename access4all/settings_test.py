# flake8: noqa
from .settings import *


DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache",}}

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
