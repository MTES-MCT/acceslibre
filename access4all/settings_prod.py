# flake8: noqa
from .settings import *

DEBUG = False

ALLOWED_HOSTS = [
    "access4all.osc-fr1.scalingo.io",
    "access4all.beta.gouv.fr",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",}}
