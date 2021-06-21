# flake8: noqa
import os
import sentry_sdk

from .settings import *


DEBUG = False

DATAGOUV_DOMAIN = "https://www.data.gouv.fr"
DATAGOUV_DATASET_ID = "93ae96a7-1db7-4cb4-a9f1-6d778370b640"

APP_NAME = os.environ.get("APP", "access4all")
ALLOWED_HOSTS = [
    "localhost",
    SITE_HOST,
    f"{APP_NAME}.osc-fr1.scalingo.io",
]

if SENTRY_DSN is not None:
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN, integrations=[DjangoIntegration()], environment="production"
    )

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
