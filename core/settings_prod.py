# flake8: noqa
from .settings import *

DEBUG = False

ALLOWED_HOSTS = [
    SITE_HOST,
    "access4all.osc-fr1.scalingo.io",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",}}
