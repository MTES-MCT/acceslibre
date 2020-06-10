# flake8: noqa
from .settings import *

DEBUG = False

# FIXME: this should eventually be provided by some env var
ALLOWED_HOSTS = [
    "access4all.osc-fr1.scalingo.io",
    "access4all.beta.gouv.fr",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache",}}
