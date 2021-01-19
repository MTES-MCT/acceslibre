# flake8: noqa
import os

from .settings import *

DEBUG = False
REVIEW_APP_URL = os.environ.get("CANONICAL_HOST_URL")
if REVIEW_APP_URL:
    SITE_HOST = REVIEW_APP_URL.replace("https://", "")

ALLOWED_HOSTS = [
    SITE_HOST,
    "access4all.osc-fr1.scalingo.io",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    }
}
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "cache_acceslibre",
#     }
# }

STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600
