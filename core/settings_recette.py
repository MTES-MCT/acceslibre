# flake8: noqa
import os

from .settings import *

DEBUG = False
ENVIRONMENT = "recette"

STAGING = True
SITE_NAME = "acceslibre (recette)"
SITE_HOST = "recette-access4all.osc-fr1.scalingo.io"
SITE_ROOT_URL = f"https://{SITE_HOST}"
ALLOWED_HOSTS = [SITE_HOST]

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

# FIXME: removed because of a nasty bug with dist static assets
STATICFILES_STORAGE = "core.storage.AppStaticFilesStorage"

# https://docs.djangoproject.com/fr/3.1/ref/middleware/#http-strict-transport-security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 3600
