# flake8: noqa
from .settings import *

DEBUG = False

ALLOWED_HOSTS = [
    SITE_HOST,
    "access4all*.osc-fr1.scalingo.io",
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
